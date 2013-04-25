/* begin license *
 *
 * "Meresco Solr" is a set of components and tools
 *  to integrate Solr into "Meresco."
 *
 * Copyright (C) 2013 Seecr (Seek You Too B.V.) http://seecr.nl
 * Copyright (C) 2013 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
 *
 * This file is part of "Meresco Solr"
 *
 * "Meresco Solr" is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * "Meresco Solr" is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with "Meresco Solr"; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 *
 * end license */

package org.meresco.solr;

import java.io.IOException;
import java.util.Iterator;
import java.util.HashMap;
import java.util.Map;

import org.apache.lucene.queryparser.classic.ParseException;
import org.apache.lucene.search.MatchAllDocsQuery;
import org.apache.solr.common.SolrException;
import org.apache.solr.common.params.MultiMapSolrParams;
import org.apache.solr.common.params.SolrParams;
import org.apache.solr.common.util.NamedList;
import org.apache.solr.core.SolrCore;
import org.apache.solr.handler.component.ResponseBuilder;
import org.apache.solr.handler.component.SearchComponent;
import org.apache.solr.request.SimpleFacets;
import org.apache.solr.request.SolrQueryRequest;
import org.apache.solr.search.DocSet;
import org.apache.solr.search.SolrIndexSearcher;
import org.apache.solr.util.RefCounted;


public class JoinFacetComponent extends SearchComponent {
	public int count = 0;
	private Map<String, Long> lastSearcherOpenTimes = new HashMap<String, Long>();
	private Map<String, IdSet> otherIdSets = new HashMap<String, IdSet>();
	
	@Override
	public void prepare(ResponseBuilder rb) throws IOException {
	}

	@Override
	public void process(ResponseBuilder rb) throws IOException {
		System.out.println("JoinFacetComponent.process[" + (count++) + "]");
	    if (rb.doFacets) {
	        SolrParams params = rb.req.getParams();
	        
	        Map<String, String[]> paramsMap = new HashMap<String, String[]>();
	        for (Iterator<String> iter = params.getParameterNamesIterator(); iter.hasNext();) {
	        	String name = (String) iter.next();
	        	String[] values = params.getParams(name);
	        	if ("facet.field".equals(name)) {
	        		continue;
	        	}
	        	if ("joinFacet.field".equals(name)) {
	        		continue;
	        	}
	        	paramsMap.put(name, values);
	        }        
	        
	        String[] joinFacetFields = params.getParams("joinFacet.field");
	        if (joinFacetFields == null) {
	        	return;
	        }
	        NamedList<Object> responseValues = rb.rsp.getValues(); 
	        NamedList<Object> facet_counts = (NamedList<Object>) responseValues.get("facet_counts");
	        Map<String, DocSet> coreDocSets = new HashMap<String, DocSet>();
	        for (String joinFacetField: joinFacetFields) {
	        	JoinQuery parsedJoinFacetField = null;
		        try {
		            parsedJoinFacetField = (JoinQuery) Utils.getQuery(rb.req, joinFacetField);
		        } catch (ParseException e) {
		            throw new SolrException(SolrException.ErrorCode.BAD_REQUEST, e);
		        }
		        paramsMap.put("facet.field", new String[] {parsedJoinFacetField.localQueryString});

		        String coreName = parsedJoinFacetField.coreName;
				SolrCore core = Utils.getCoreByName(rb.req, coreName);
		        RefCounted<SolrIndexSearcher> coreSearcher = Utils.getSearcher(core);
		        try {
		        	DocSet docSet = coreDocSets.get(coreName);
		        	if (docSet == null) {
		        		docSet = docSetForJoin(rb, parsedJoinFacetField, coreSearcher.get());
		        		coreDocSets.put(coreName, docSet);
		        	}
					SimpleFacets f = new JoinSimpleFacets(
		        		rb.req,
		                docSet,
		                new MultiMapSolrParams(paramsMap),
		                rb,
		                coreSearcher.get());
			        updateCounts(facet_counts, f.getFacetCounts());
		        }
		        finally {
		        	coreSearcher.decref();
		        	core.close();
		        }
	        }

//	        String[] pivots = params.getParams( FacetParams.FACET_PIVOT );
//	        if( pivots != null && pivots.length > 0 ) {
//	          NamedList v = pivotHelper.process(rb, params, pivots);
//	          if( v != null ) {
//	            counts.add( PIVOT_KEY, v );
//	          }
//	        }
	    }
	}

	private DocSet docSetForJoin(ResponseBuilder rb, JoinQuery parsedJoinFacetField, SolrIndexSearcher coreSearcher) throws IOException {
		DocSet givenDocSet = rb.getResults().docSet;
        IdSet givenIdSet = IdSet.idSetFromDocSet(givenDocSet, rb.req.getSearcher(), parsedJoinFacetField.toField);
        System.out.println("given fetchValuesTime " + givenIdSet.fetchValuesTime);
        System.out.println("given docSetNext time " + givenIdSet.docSetNextTime);
        System.out.println("given datastructureTime " + givenIdSet.dataStructureTime);
        
		IdSet otherIdSet = makeOtherDocSet(parsedJoinFacetField, coreSearcher);
        
        givenIdSet.retainAll(otherIdSet);
        System.out.println("intersect time " + givenIdSet.intersectionTime);
        DocSet docSet = givenIdSet.makeDocSet(otherIdSet);
        System.out.println("makeDocSet time " + givenIdSet.makeDocSetTime);
        return docSet;
	}

	private IdSet makeOtherDocSet(JoinQuery parsedJoinFacetField,
			SolrIndexSearcher coreSearcher) throws IOException {
		String coreName = parsedJoinFacetField.coreName;
		long searcherOpenTime = coreSearcher.getOpenTime();
		Long previousOpenTime = lastSearcherOpenTimes.get(coreName);
		if (previousOpenTime != null && previousOpenTime == searcherOpenTime) {
			return otherIdSets.get(coreName);
		}
		DocSet otherDocSet = coreSearcher.getDocSet(new MatchAllDocsQuery());
        IdSet otherIdSet = IdSet.idSetFromDocSet(otherDocSet, coreSearcher, parsedJoinFacetField.fromField);
        otherIdSets.put(coreName, otherIdSet);
        lastSearcherOpenTimes.put(coreName, searcherOpenTime);
        System.out.println("other fetchValuesTime " + otherIdSet.fetchValuesTime);
        System.out.println("other docSetNext time " + otherIdSet.docSetNextTime);
        System.out.println("other datastructureTime " + otherIdSet.dataStructureTime);
		return otherIdSet;
	}

	private void updateCounts(NamedList<Object> counts, NamedList<Object> newCounts) {
		for (Iterator<Map.Entry<String, Object>> iterator = newCounts.iterator(); iterator.hasNext(); ) {
			Map.Entry<String, Object> entry = iterator.next();
			String countsName = entry.getKey();		
			NamedList<Object> newCountValues = (NamedList<Object>) entry.getValue();
			NamedList<Object> existingCountValues = (NamedList<Object>) counts.get(countsName);
			if (existingCountValues == null) {
				counts.add(countsName, newCountValues);
			} else {
				existingCountValues.addAll(newCountValues);
			}
		}
	}
	
	@Override
	public String getDescription() {
		return "Facets on joined core";
	}

	@Override
	public String getSource() {
		return "Meresco";
	}

	class JoinSimpleFacets extends SimpleFacets {
		public JoinSimpleFacets(
				 SolrQueryRequest req,
                 DocSet docs,
                 SolrParams params,
                 ResponseBuilder rb,
                 SolrIndexSearcher searcher) {
			super(req, docs, params, rb);
			this.searcher = searcher;
		}
	}
}
