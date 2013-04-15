package org.meresco.solr;

import org.apache.lucene.search.Query;
import org.apache.solr.common.SolrException;
import org.apache.solr.common.params.SolrParams;
import org.apache.solr.common.util.NamedList;
import org.apache.solr.core.CoreContainer;
import org.apache.solr.core.SolrCore;
import org.apache.solr.request.LocalSolrQueryRequest;
import org.apache.solr.request.SolrQueryRequest;
import org.apache.solr.search.QParser;
import org.apache.solr.search.QParserPlugin;
import org.apache.solr.search.SolrIndexSearcher;
import org.apache.solr.util.RefCounted;
import org.apache.lucene.queryparser.classic.ParseException;

public class JoinParserPlugin extends QParserPlugin {
    //Copied from JoinQParserPlugin
    public static String NAME = "myjoin";

    @Override
    public void init(NamedList args) {
    }

    @Override
    public QParser createParser(String qstr, SolrParams localParams, SolrParams params, SolrQueryRequest req) {
        return new QParser(qstr, localParams, params, req) {
            public Query parse() throws ParseException {
                String core = getParam("core");
                String v = localParams.get("v");
                Query fromQuery;
                // long fromCoreOpenTime = 0;

                if (!core.equals(req.getCore().getCoreDescriptor().getName()) ) {
                    CoreContainer container = req.getCore().getCoreDescriptor().getCoreContainer();

                    final SolrCore fromCore = container.getCore(core);
                    RefCounted<SolrIndexSearcher> fromHolder = null;

                    if (fromCore == null) {
                        throw new SolrException(SolrException.ErrorCode.BAD_REQUEST, "Cross-core join: no such core " + core);
                    }

                    LocalSolrQueryRequest otherReq = new LocalSolrQueryRequest(fromCore, params);
                    try {
                        QParser parser = QParser.getParser(v, "lucene", otherReq);
                        fromQuery = parser.getQuery();
                        fromHolder = fromCore.getRegisteredSearcher();
                        // if (fromHolder != null) fromCoreOpenTime = fromHolder.get().getOpenTime();
                    } finally {
                        otherReq.close();
                        fromCore.close();
                        if (fromHolder != null) fromHolder.decref();
                    }
                } else {
                    QParser fromQueryParser = subQuery(v, null);
                    fromQuery = fromQueryParser.getQuery();
                }

                JoinQuery jq = new JoinQuery(core, fromQuery);
                // jq.fromCoreOpenTime = fromCoreOpenTime;
                return jq;
            }
        };
    }
}

class JoinQuery extends Query {
    String core;
    Query query;

    public JoinQuery(String core, Query query) {
        this.core = core;
        this.query = query;
    }

    @Override
    public String toString(String arg0) {
        // TODO Auto-generated method stub
        return null;
    }
}