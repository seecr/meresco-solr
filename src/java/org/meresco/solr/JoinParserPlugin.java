package org.meresco.solr;

import java.io.IOException;

import org.apache.lucene.search.DocIdSet;
import org.apache.lucene.search.DocIdSetIterator;
import org.apache.lucene.search.Explanation;
import org.apache.lucene.search.Filter;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.search.Query;
import org.apache.lucene.search.Scorer;
import org.apache.lucene.search.Weight;
import org.apache.lucene.util.Bits;
import org.apache.solr.common.SolrException;
import org.apache.solr.common.params.SolrParams;
import org.apache.solr.common.util.NamedList;
import org.apache.solr.core.CoreContainer;
import org.apache.solr.core.CoreDescriptor;
import org.apache.solr.core.SolrCore;
import org.apache.solr.request.LocalSolrQueryRequest;
import org.apache.solr.request.SolrQueryRequest;
import org.apache.solr.search.DocSet;
import org.apache.solr.search.QParser;
import org.apache.solr.search.QParserPlugin;
import org.apache.solr.search.SolrIndexSearcher;
import org.apache.solr.util.RefCounted;
import org.apache.lucene.index.AtomicReaderContext;
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
                Query query;

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
                    LocalSolrQueryRequest otherReq = new LocalSolrQueryRequest(otherCore, params);
                    try {
                        query = QParser.getParser(localQueryString, "lucene", otherReq).getQuery();
                    } finally {
                        otherReq.close();
                      	otherCore.close();
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
    
    public void setQuery(Query q) {
    	this.query = q;
    }
}