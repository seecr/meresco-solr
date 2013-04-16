package org.meresco.solr;

import java.io.IOException;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;
import java.util.HashSet;

import org.apache.lucene.document.Document;
import org.apache.lucene.queryparser.classic.ParseException;
import org.apache.lucene.search.Query;
import org.apache.solr.common.SolrException;
import org.apache.solr.common.params.SolrParams;
import org.apache.solr.core.CoreContainer;
import org.apache.solr.core.SolrCore;
import org.apache.solr.handler.component.ResponseBuilder;
import org.apache.solr.handler.component.SearchComponent;
import org.apache.solr.request.SolrQueryRequest;
import org.apache.solr.response.ResultContext;
import org.apache.solr.response.SolrQueryResponse;
import org.apache.solr.search.DocIterator;
import org.apache.solr.search.DocListAndSet;
import org.apache.solr.search.DocSet;
import org.apache.solr.search.DocSlice;
import org.apache.solr.search.HashDocSet;
import org.apache.solr.search.QParser;
import org.apache.solr.search.SolrIndexSearcher;
import org.apache.solr.util.RefCounted;


public class JoinComponent extends SearchComponent {
	private Set<String> ID_FIELDS = new HashSet<String>() {{ this.add("__id__"); }};

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
        rb.setNeedDocSet( true );
    }

    @Override
    public void process(ResponseBuilder rb) throws IOException {
        SolrQueryRequest req = rb.req;
        SolrParams params = req.getParams();
        SolrQueryResponse rsp = rb.rsp;

        DocSet docSet = rb.getResults().docSet;
        SolrIndexSearcher searcher = req.getSearcher();
        IdSet idSet = idSetFromDocSet(docSet, searcher);

        DocSet otherDocSet = null;
        String join = params.get("join");
        JoinQuery joinQuery = null;
        try {
            joinQuery = (JoinQuery) getQuery(req, join);
        } catch (ParseException e) {
            throw new SolrException(SolrException.ErrorCode.BAD_REQUEST, e);
        }

        SolrIndexSearcher coreSearcher = searcherForCore(req, joinQuery.core);
        otherDocSet = coreSearcher.getDocSet(joinQuery.query);
        IdSet otherIdSet = idSetFromDocSet(otherDocSet, coreSearcher);
        IdSet idIntersection = idSet.intersect(otherIdSet);

        JoinDocSet joinDocSet = new JoinDocSet(
        		idIntersection.getDocSet(), 
        		idIntersection.getDocSetForIds(otherIdSet));
        
        DocListAndSet res = new DocListAndSet();
        res.docList = docList(luceneIdsFromDocset(joinDocSet));
        res.docSet = joinDocSet;
        rb.setResults(res);

        ResultContext ctx = new ResultContext();
        ctx.docs = rb.getResults().docList;
        ctx.query = null; // anything?
        rsp.add("joinResponse", ctx);
        return;
    }

    private IdSet idSetFromDocSet(DocSet docSet, SolrIndexSearcher searcher) {
    	IdSet idSet = new IdSet();
    	DocIterator iter = docSet.iterator();
    	while (iter.hasNext()) {
    		int docId = iter.nextDoc();
    		idSet.add(idForDocId(docId, searcher), docId);
    	}
    	return idSet;
	}

	private int idForDocId(int docId, SolrIndexSearcher searcher) {
		Document doc = null;
		try {
			doc = searcher.doc(docId, ID_FIELDS);
		} catch (IOException e) {
			throw new SolrException(SolrException.ErrorCode.SERVER_ERROR, e);
		}
		return doc.get("__id__").hashCode();
	}

	public static SolrIndexSearcher searcherForCore(SolrQueryRequest req, String name) {
        //Copied from JoinQParserPlugin
        CoreContainer container = req.getCore().getCoreDescriptor().getCoreContainer();
        SolrCore core = container.getCore(name);
        // This could block if there is a static warming query with a join in it, and if useColdSearcher is true.
        // Deadlock could result if two cores both had useColdSearcher and had joins that used eachother.
        // This would be very predictable though (should happen every time if misconfigured)
        RefCounted<SolrIndexSearcher> fromRef = core.getSearcher(false, true, null);

        // be careful not to do anything with this searcher that requires the thread local
        // SolrRequestInfo in a manner that requires the core in the request to match
        return fromRef.get();
    }

    public static Query getQuery(SolrQueryRequest req, String queryParameter) throws ParseException {
        QParser parser = QParser.getParser(queryParameter, null, req);
        System.out.println("parser: " + queryParameter + ":" + parser.getClass().getName());
        return parser.getQuery();
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
    
    private class IdSet {
    	private Map<Integer, Integer> id2docId = new HashMap<Integer, Integer>();

    	public void add(int id, int docId) {
    		id2docId.put(id, docId);
    	}

    	public int size() {
    		return id2docId.size();
    	}

    	public Set<Integer> ids() {
    		return id2docId.keySet();
    	}

    	public Iterator<Integer> iterator() {
    		return ids().iterator();
    	}

    	public IdSet intersect(IdSet idSet) {
    		IdSet result = new IdSet();
    		Set<Integer> newKeys = new HashSet<Integer>(id2docId.keySet());
    		newKeys.retainAll(idSet.ids());
    		for (Iterator<Integer> iter = newKeys.iterator(); iter.hasNext();) {
    			int id = iter.next();
    			result.add(id, id2docId.get(id));
    		}
    		return result;
    	}

    	public DocSet getDocSetForIds(IdSet ids) {
        	int[] docIds = new int[ids.size()];
        	int docs = 0;
        	Iterator<Integer> iter = ids.iterator();
        	while (iter.hasNext()) {
        		docIds[docs++] = id2docId.get(iter.next());
        	}
    		return new HashDocSet(docIds, 0, ids.size());
    	}

    	public DocSet getDocSet() {
    		return getDocSetForIds(this);
    	}
    }
}
