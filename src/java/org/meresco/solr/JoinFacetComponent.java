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
import java.util.List;
import java.util.Map;

import org.apache.lucene.queryparser.classic.ParseException;
import org.apache.lucene.search.FieldCache;
import org.apache.solr.common.SolrException;
import org.apache.solr.common.params.MultiMapSolrParams;
import org.apache.solr.common.params.SolrParams;
import org.apache.solr.common.util.NamedList;
import org.apache.solr.core.SolrCore;
import org.apache.solr.handler.component.ResponseBuilder;
import org.apache.solr.handler.component.SearchComponent;
import org.apache.solr.request.SimpleFacets;
import org.apache.solr.request.SolrQueryRequest;
import org.apache.solr.search.DocIterator;
import org.apache.solr.search.DocSet;
import org.apache.solr.search.HashDocSet;
import org.apache.solr.search.SolrIndexSearcher;
import org.apache.solr.util.RefCounted;


public class JoinFacetComponent extends SearchComponent {
	private Map<String, Long> lastSearcherOpenTimes = new HashMap<String, Long>();
	private Map<String, Uid2DocIdsMap> uid2DocIdsMaps = new HashMap<String, Uid2DocIdsMap>();
	
	@Override
	public void prepare(ResponseBuilder rb) throws IOException {
	}

	@Override
	public void process(ResponseBuilder rb) throws IOException {
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
	        Map<String, DocSet> joinCoreDocSets = new HashMap<String, DocSet>();
	        for (String joinFacetField: joinFacetFields) {
	        	JoinQuery parsedJoinFacetField = null;
		        try {
		            parsedJoinFacetField = (JoinQuery) Utils.getQuery(rb.req, joinFacetField);
		        } catch (ParseException e) {
		            throw new SolrException(SolrException.ErrorCode.BAD_REQUEST, e);
		        }
		        paramsMap.put("facet.field", new String[] {parsedJoinFacetField.localQueryString});

		        String coreName = parsedJoinFacetField.coreName;
        		String joinKey = coreName + "###" + parsedJoinFacetField.fromField + ":" + parsedJoinFacetField.toField;
		        SolrCore core = Utils.getCoreByName(rb.req, coreName);
		        RefCounted<SolrIndexSearcher> coreSearcher = Utils.getSearcher(core);
		        try {
		        	DocSet docSet = joinCoreDocSets.get(joinKey);
		        	if (docSet == null) {
		        		Uid2DocIdsMap uid2DocIdsMap = uid2DocIdsMap(coreName, parsedJoinFacetField.fromField, coreSearcher.get());
						docSet = mapToOtherCore(rb.getResults().docSet, parsedJoinFacetField.toField, rb.req.getSearcher(), uid2DocIdsMap);
						joinCoreDocSets.put(joinKey, docSet);
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

	private Uid2DocIdsMap uid2DocIdsMap(String coreName, String fromField, SolrIndexSearcher coreSearcher) throws IOException {
		String key = coreName + "###" + fromField;
		long searcherOpenTime = coreSearcher.getOpenTime();
		Long previousOpenTime = lastSearcherOpenTimes.get(key);
		if (previousOpenTime != null && previousOpenTime == searcherOpenTime) {
			return uid2DocIdsMaps.get(key);
		}
        Uid2DocIdsMap uid2DocIdsMap = new Uid2DocIdsMap(coreSearcher, fromField);
        uid2DocIdsMaps.put(key, uid2DocIdsMap);
        lastSearcherOpenTimes.put(key, searcherOpenTime);
		return uid2DocIdsMap;
	}	
	
	private DocSet mapToOtherCore(DocSet docSet, String toField, SolrIndexSearcher searcher, Uid2DocIdsMap uid2DocIdsMap) {
    	int[] docIds = new int[uid2DocIdsMap.numberOfDocIds];
    	int docs = 0;
		try {
			long[] uidFieldValues = FieldCache.DEFAULT.getLongs(searcher.getAtomicReader(), toField, true);
			for (DocIterator iterator = docSet.iterator(); iterator.hasNext();) {
				int docId = (int) iterator.nextDoc();
				long uid = uidFieldValues[docId];
				if (uid == 0) {
					throw new SolrException(SolrException.ErrorCode.BAD_REQUEST, "Field " + toField + " is not a numeric field.");
				}
	    		List<Integer> mappingDocIds = uid2DocIdsMap.uid2docIds.get(uid);
	    		if (mappingDocIds != null) {
	    			for (Iterator<Integer> docIdsIter = mappingDocIds.iterator(); docIdsIter.hasNext();) {
	    				docIds[docs++] = docIdsIter.next();
	    			}
	    		}
			}
    		return new HashDocSet(docIds, 0, docs);
		} catch (IOException e) {
			throw new SolrException(SolrException.ErrorCode.SERVER_ERROR, e);
		} catch (NumberFormatException e) {
			throw new SolrException(SolrException.ErrorCode.BAD_REQUEST, "Field " + toField + " is unknown or not a long field.");
		}
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
