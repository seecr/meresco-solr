package org.meresco.solr;

import java.io.IOException;
import java.util.Iterator;
import java.util.HashMap;
import java.util.Map;


import org.apache.lucene.queryparser.classic.ParseException;
import org.apache.solr.common.SolrException;
import org.apache.solr.common.params.MultiMapSolrParams;
import org.apache.solr.common.params.SolrParams;
import org.apache.solr.common.util.NamedList;
import org.apache.solr.handler.component.ResponseBuilder;
import org.apache.solr.handler.component.SearchComponent;
import org.apache.solr.request.SimpleFacets;
import org.apache.solr.request.SolrQueryRequest;
import org.apache.solr.search.DocSet;


public class JoinFacetComponent extends SearchComponent {
	@Override
	public void prepare(ResponseBuilder rb) throws IOException {
	}

	@Override
	public void process(ResponseBuilder rb) throws IOException {
	    if (rb.doFacets) {
	        SolrParams params = rb.req.getParams();
	        
	        String joinFacetField = params.get("joinFacet.field");
	        JoinQuery parsedJoinFacetField = null;
	        try {
	            parsedJoinFacetField = (JoinQuery) JoinComponent.getQuery(rb.req, joinFacetField);
	        } catch (ParseException e) {
	            throw new SolrException(SolrException.ErrorCode.BAD_REQUEST, e);
	        }	        
	        
	        Map<String, String[]> paramsMap = new HashMap<String, String[]>();
	        for (Iterator<String> iter = params.getParameterNamesIterator(); iter.hasNext();) {
	        	String name = (String) iter.next();
	        	String[] values = params.getParams(name);
	        	if ("facet.field".equals(name)) {
	        		continue;
	        	}
	        	if ("joinFacet.field".equals(name)) {
	        		name = "facet.field";
	        		values = new String[] {parsedJoinFacetField.v};
	        	}
	        	paramsMap.put(name, values);
	        }

	        SimpleFacets f = new JoinSimpleFacets(rb.req,
	                ((JoinDocSet)rb.getResults().docSet).getOtherCoreDocSet(),
	                new MultiMapSolrParams(paramsMap),
	                rb,
	                parsedJoinFacetField.core);

	        NamedList<Object> counts = f.getFacetCounts();
//	        String[] pivots = params.getParams( FacetParams.FACET_PIVOT );
//	        if( pivots != null && pivots.length > 0 ) {
//	          NamedList v = pivotHelper.process(rb, params, pivots);
//	          if( v != null ) {
//	            counts.add( PIVOT_KEY, v );
//	          }
//	        }

	        rb.rsp.add( "join_facet_counts", counts );
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
                 String core) {
			super(req, docs, params, rb);
			this.searcher = JoinComponent.searcherForCore(req, core);
		 }
	}
}
