package org.meresco.solr;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.HashMap;
import java.util.List;
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
	        Map<String, DocSet> coreDocSets = new HashMap<String, DocSet>();
	        for (String joinFacetField: joinFacetFields) {
	        	JoinQuery parsedJoinFacetField = null;
		        try {
		            parsedJoinFacetField = (JoinQuery) JoinComponent.getQuery(rb.req, joinFacetField);
		        } catch (ParseException e) {
		            throw new SolrException(SolrException.ErrorCode.BAD_REQUEST, e);
		        }
		        paramsMap.put("facet.field", new String[] {parsedJoinFacetField.localQueryString});

		        String coreName = parsedJoinFacetField.coreName;
				SolrCore core = JoinComponent.getCoreByName(rb.req, coreName);
		        RefCounted<SolrIndexSearcher> coreSearcher = JoinComponent.getSearcher(core);
		        try {
		        	DocSet docSet = coreDocSets.get(coreName);
		        	if (docSet == null) {
		        		docSet = docSetForCore(rb, coreName, coreSearcher.get());
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

	private DocSet docSetForCore(ResponseBuilder rb, String coreName, SolrIndexSearcher coreSearcher) throws IOException {
		DocSet docSet = null;
		DocSet givenDocSet = rb.getResults().docSet;
		if (givenDocSet instanceof JoinDocSet) {
			docSet = ((JoinDocSet) givenDocSet).getOtherCoreDocSet(coreName);
		}
		if (docSet == null) {
            DocSet otherDocSet = coreSearcher.getDocSet(new MatchAllDocsQuery());
            IdSet otherIdSet = IdSet.idSetFromDocSet(otherDocSet, coreSearcher);
            IdSet givenDocSetIds = IdSet.idSetFromDocSet(givenDocSet, rb.req.getSearcher());
            otherIdSet.retainAll(givenDocSetIds);
            docSet = otherIdSet.makeDocSet();
		}
		return docSet;
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
