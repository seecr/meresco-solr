package org.meresco.solr;

import org.apache.lucene.search.Query;
import org.apache.solr.common.SolrException;
import org.apache.solr.common.params.SolrParams;
import org.apache.solr.common.util.NamedList;
import org.apache.solr.core.CoreContainer;
import org.apache.solr.core.CoreDescriptor;
import org.apache.solr.core.SolrCore;
import org.apache.solr.request.LocalSolrQueryRequest;
import org.apache.solr.request.SolrQueryRequest;
import org.apache.solr.search.QParser;
import org.apache.solr.search.QParserPlugin;
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
                String otherCoreName = getParam("core");
                String v = localParams.get("v");
                Query query;

                CoreDescriptor coreDescriptor = req.getCore().getCoreDescriptor();
                if (otherCoreName.equals(coreDescriptor.getName()) ) {
                    query = subQuery(v, null).getQuery();	
                }
                else {
                    CoreContainer container = coreDescriptor.getCoreContainer();
                    final SolrCore otherCore = container.getCore(otherCoreName);
                    if (otherCore == null) {
                        throw new SolrException(SolrException.ErrorCode.BAD_REQUEST, "Cross-core join: no such core " + otherCoreName);
                    }
                    LocalSolrQueryRequest otherReq = new LocalSolrQueryRequest(otherCore, params);
                    try {
                        query = QParser.getParser(v, "lucene", otherReq).getQuery();
                    } finally {
                        otherReq.close();
                        otherCore.close();
                    }
                }
                return new JoinQuery(otherCoreName, query, v);
            }
        };
    }
}

class JoinQuery extends Query {
    String core;
    Query query;
    String v;

    public JoinQuery(String core, Query query, String v) {
        this.core = core;
        this.query = query;
        this.v = v;
    }

    @Override
    public String toString(String arg0) {
       return core + ":" + query;
    }
}