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
