package org.meresco.solr;

import org.apache.lucene.queryparser.classic.ParseException;
import org.apache.lucene.search.Query;
import org.apache.solr.core.CoreContainer;
import org.apache.solr.core.SolrCore;
import org.apache.solr.request.SolrQueryRequest;
import org.apache.solr.search.QParser;
import org.apache.solr.search.SolrIndexSearcher;
import org.apache.solr.util.RefCounted;

public class Utils {

    public static Query getQuery(SolrQueryRequest req, String queryParameter) throws ParseException {
        QParser parser = QParser.getParser(queryParameter, null, req);
        return parser.getQuery();
    }
    

    /**
     * Returned RefCounted<SolrIndexSearcher> instance must be decref'ed!
     */
    public static RefCounted<SolrIndexSearcher> getSearcher(SolrCore core) {
        return core.getSearcher(false, true, null);
    }

    /**
     * Returned core must be closed!
     */
	public static SolrCore getCoreByName(SolrQueryRequest req, String name) {
        CoreContainer container = req.getCore().getCoreDescriptor().getCoreContainer();
        return container.getCore(name);
	}

    /**
     * Returned core must be closed!
     */
	public static SolrCore getCoreByName(SolrIndexSearcher searcher, String name) {
        CoreContainer container = searcher.getCore().getCoreDescriptor().getCoreContainer();
        return container.getCore(name);
	}
}
