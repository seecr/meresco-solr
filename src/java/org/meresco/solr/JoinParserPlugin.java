/* begin license *
 *
 * "Meresco Solr" is a set of components and tools
 *  to integrate Solr into "Meresco."
 *
 * Copyright (C) 2013 Seecr (Seek You Too B.V.) http://seecr.nl
 * Copyright (C) 2013 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
 *
 * This file is part of "Meresco Solr"
 *
 * "Meresco Solr" is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * "Meresco Solr" is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with "Meresco Solr"; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 *
 * end license */

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
    public static String NAME = "facetjoin";
    public static String DEFAULT_JOIN_FIELD = "__id__";

    @Override
    public void init(NamedList args) {
    }

    @Override
    public QParser createParser(String qstr, SolrParams localParams, SolrParams params, SolrQueryRequest req) {
        return new QParser(qstr, localParams, params, req) {
            public Query parse() throws ParseException {
                String otherCoreName = getParam("core");
                String fromField = getParam("from");
                if (fromField == null) {
                	fromField = DEFAULT_JOIN_FIELD;
                }
                String toField = getParam("to");
                if (toField == null) {
                	toField = DEFAULT_JOIN_FIELD;
                }
                String localQueryString = localParams.get("v");

                CoreDescriptor coreDescriptor = req.getCore().getCoreDescriptor();
                if (!otherCoreName.equals(coreDescriptor.getName())) {
                    CoreContainer container = coreDescriptor.getCoreContainer();
                    final SolrCore otherCore = container.getCore(otherCoreName);
                    if (otherCore == null) {
                        throw new SolrException(SolrException.ErrorCode.BAD_REQUEST, "Cross-core join: no such core " + otherCoreName);
                    }
                }
                Query query = new JoinQuery(otherCoreName, fromField, toField, localQueryString);
                return query;
            }
        };
    }
}


class JoinQuery extends Query {
	String coreName;
	String fromField;
	String toField;
    String localQueryString;

    public JoinQuery(String coreName, String fromField, String toField, String localQueryString) {
        this.coreName = coreName;
        this.fromField = fromField;
        this.toField = toField;
        this.localQueryString = localQueryString;
    }

    @Override
    public String toString(String arg0) {
       return String.format(
    		   "{!%s core=%s from=%s to=%s}%s", 
    		   JoinParserPlugin.NAME, coreName, fromField, toField, localQueryString);
    }   
}