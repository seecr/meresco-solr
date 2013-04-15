package org.meresco.solr;

import java.io.IOException;

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
import org.apache.solr.search.DocSet;
import org.apache.solr.search.DocSlice;
import org.apache.solr.search.QParser;
import org.apache.solr.search.SolrIndexSearcher;
import org.apache.solr.util.RefCounted;


public class JoinComponent extends SearchComponent {

    @Override
    public String getDescription() {
        return "hallo";
    }

    @Override
    public String getSource() {
        return "no-source";
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
        DocSet otherDocSet = null;
        String join = params.get("join");
        JoinQuery joinQuery = null;
        try {
            joinQuery = (JoinQuery) getQuery(req, join);
        } catch (ParseException e) {
            throw new SolrException(SolrException.ErrorCode.BAD_REQUEST, e);
        }

        SolrIndexSearcher fromSearcher = searcherForCore(req, joinQuery.core);
        otherDocSet = fromSearcher.getDocSet(joinQuery.query);
        DocSet intersection = docSet.intersection(otherDocSet);

        ResultContext ctx = new ResultContext();
        ctx.docs = docList(luceneIdsFromDocset(intersection));
        ctx.query = null; // anything?
        rsp.add("joinResponse", ctx);
        return;
    }

    private SolrIndexSearcher searcherForCore(SolrQueryRequest req, String name) {
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

    private Query getQuery(SolrQueryRequest req, String otherQuery) throws ParseException {
        QParser parser = QParser.getParser(otherQuery, null, req);
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
            luceneIds[docs++] = iterator.next();
        }
        return luceneIds;
    }
}
