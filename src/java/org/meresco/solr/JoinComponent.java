package org.meresco.solr;

import java.io.IOException;
import java.util.HashMap;
import java.util.Iterator;

import org.apache.lucene.queryparser.classic.ParseException;
import org.apache.lucene.search.Query;
import org.apache.solr.common.SolrException;
import org.apache.solr.common.params.SolrParams;
import org.apache.solr.common.util.NamedList;
import org.apache.solr.core.CoreContainer;
import org.apache.solr.core.SolrCore;
import org.apache.solr.handler.component.ResponseBuilder;
import org.apache.solr.handler.component.SearchComponent;
import org.apache.solr.request.LocalSolrQueryRequest;
import org.apache.solr.request.SolrQueryRequest;
import org.apache.solr.response.ResultContext;
import org.apache.solr.response.SolrQueryResponse;
import org.apache.solr.search.DocIterator;
import org.apache.solr.search.DocListAndSet;
import org.apache.solr.search.DocSet;
import org.apache.solr.search.DocSlice;
import org.apache.solr.search.QParser;
import org.apache.solr.search.SolrIndexSearcher;
import org.apache.solr.util.RefCounted;


public class JoinComponent extends SearchComponent {
	@Override
    public String getDescription() {
        return "join on other core that supports facets on that core";
    }

    @Override
    public String getSource() {
        return "Meresco";
    }

    @Override
    public void prepare(ResponseBuilder rb) throws IOException {
    	String[] joins = rb.req.getParams().getParams("join");
        if (joins != null) {
        	rb.setNeedDocSet( true );
        }
    }

    @Override
    public void process(ResponseBuilder rb) throws IOException {
        SolrQueryRequest req = rb.req;
        SolrParams params = req.getParams();
        String[] joins = params.getParams("join");
        if (joins == null) {
        	return;
        }
        SolrQueryResponse rsp = rb.rsp;
        
        DocSet docSet = rb.getResults().docSet;
        IdSet idIntersection = IdSet.idSetFromDocSet(docSet, req.getSearcher());
        HashMap<String, IdSet> core2IdSet = new HashMap<String, IdSet>();
        
        for (String join : joins) {
        	JoinQuery joinQuery = null;
        	SolrCore core = null;
            try {
                joinQuery = (JoinQuery) Utils.getQuery(req, join);
                core = Utils.getCoreByName(req, joinQuery.coreName);
                joinQuery.setQuery(parseQuery(joinQuery.localQueryString, core, params));
            } catch (ParseException e) {
                throw new SolrException(SolrException.ErrorCode.BAD_REQUEST, e);
            } catch (ClassCastException e) {
                throw new SolrException(SolrException.ErrorCode.BAD_REQUEST, "Not a valid join query: " + join);
            }
            
            
            RefCounted<SolrIndexSearcher> coreSearcher = Utils.getSearcher(core);
            try {
	            DocSet otherDocSet = coreSearcher.get().getDocSet(joinQuery.query);
	            IdSet otherIdSet = IdSet.idSetFromDocSet(otherDocSet, coreSearcher.get());
	            core2IdSet.put(joinQuery.coreName, otherIdSet);
	            idIntersection.retainAll(otherIdSet);
            } finally {
            	coreSearcher.decref();
            	core.close();
            }
        }
       
        HashMap<String, DocSet> core2DocSet = new HashMap<String, DocSet>();
        for (Iterator<String> iterator = core2IdSet.keySet().iterator(); iterator.hasNext(); ) {
        	String core = iterator.next();
        	core2DocSet.put(core, idIntersection.makeDocSet(core2IdSet.get(core)));
        }
        JoinDocSet joinDocSet = new JoinDocSet(
    		idIntersection, 
    		core2DocSet
    	);
        DocListAndSet res = new DocListAndSet();
        res.docList = docList(luceneIdsFromDocset(joinDocSet));
        res.docSet = joinDocSet;
        rb.setResults(res);

		NamedList<Object> responseValues = rsp.getValues(); 
        responseValues.remove("response");
        ResultContext ctx = new ResultContext();
        ctx.docs = rb.getResults().docList;
        ctx.query = null; // anything?
        responseValues.add("response", ctx);
    }
    
    private Query parseQuery(String query, SolrCore core, SolrParams params) throws ParseException {
    	LocalSolrQueryRequest otherReq = new LocalSolrQueryRequest(core, params);
        try {
            return QParser.getParser(query, "lucene", otherReq).getQuery();
        } finally {
            otherReq.close();
        }
    }

    private DocSlice docList(int[] luceneIds) {
        int numDocs = luceneIds.length;
        return new DocSlice(0, numDocs, luceneIds, null, numDocs, 0);
    }

    private int[] luceneIdsFromDocset(DocSet docSet) {
        DocIterator iterator = docSet.iterator();
        int[] luceneIds = new int[docSet.size()];
        int docs = 0;
        while (iterator.hasNext()) {
            luceneIds[docs++] = iterator.nextDoc();
        }
        return luceneIds;
    }
}
