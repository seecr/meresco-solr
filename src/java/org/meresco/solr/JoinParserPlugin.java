package org.meresco.solr;

import org.apache.lucene.search.Query;
import org.apache.solr.common.SolrException;
import org.apache.solr.common.params.SolrParams;
import org.apache.solr.common.util.NamedList;
import org.apache.solr.core.CoreContainer;
import org.apache.solr.core.CoreDescriptor;
import org.apache.solr.core.SolrCore;
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
                String localQueryString = localParams.get("v");

                CoreDescriptor coreDescriptor = req.getCore().getCoreDescriptor();
                if (otherCoreName.equals(coreDescriptor.getName()) ) {
                    query = subQuery(localQueryString, null).getQuery();	
                }
                else {
                    CoreContainer container = coreDescriptor.getCoreContainer();
                    final SolrCore otherCore = container.getCore(otherCoreName);
                    if (otherCore == null) {
                        throw new SolrException(SolrException.ErrorCode.BAD_REQUEST, "Cross-core join: no such core " + otherCoreName);
                    }
                }
                return new JoinQuery(otherCoreName, localQueryString);
            }
        };
    }
}


class JoinQuery extends Query {
	String coreName;
    String localQueryString;
    Query query = null;

    public JoinQuery(String coreName, String localQueryString) {
        this.coreName = coreName;
        this.localQueryString = localQueryString;
    }

    @Override
    public String toString(String arg0) {
       return coreName + ":" + this.localQueryString;
    }   
}