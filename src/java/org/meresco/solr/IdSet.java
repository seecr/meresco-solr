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

import java.io.IOException;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;

import org.apache.lucene.document.Document;
import org.apache.solr.common.SolrException;
import org.apache.solr.search.DocIterator;
import org.apache.solr.search.DocSet;
import org.apache.solr.search.HashDocSet;
import org.apache.solr.search.SolrIndexSearcher;


public class IdSet {
	private String idFieldName;
	private Set<String> idFieldSet;
	private Set<Integer> ids = new HashSet<Integer>();
	private Map<Integer, Integer> id2docId = new HashMap<Integer, Integer>();
	
	private IdSet(DocSet docSet, SolrIndexSearcher searcher, final String idFieldName) {
		System.out.println("nieuw IdSet: " + idFieldName);
		this.idFieldName = idFieldName;
		this.idFieldSet = new HashSet<String>() {{ this.add(idFieldName); }};
		for (DocIterator iterator = docSet.iterator(); iterator.hasNext();) {
			int docId = (int) iterator.nextDoc();
			int id = idForDocId(docId, searcher);
			ids.add(id);
			id2docId.put(id, docId);
		}	
	}
	
	public static IdSet idSetFromDocSet(DocSet docSet, SolrIndexSearcher searcher, String idFieldName) {
		if (docSet instanceof JoinDocSet) {
			return ((JoinDocSet) docSet).getIdSet();
		}
		return new IdSet(docSet, searcher, idFieldName);
	}
	
	public int getDocId(int id) {
		return id2docId.get(id);
	}

	public Set<Integer> ids() {
		return ids;
	}
		
	public void retainAll(IdSet idSet) {
		ids.retainAll(idSet.ids());
	}

	public DocSet makeDocSet(IdSet mapping) {
		int length = ids.size();
    	int[] docIds = new int[length];
    	int docs = 0;
    	Iterator<Integer> iter = ids.iterator();
    	while (iter.hasNext()) {
    		docIds[docs++] = mapping.getDocId(iter.next());
    	}
		return new HashDocSet(docIds, 0, length);
	}

	public DocSet makeDocSet() {
		return makeDocSet(this);
	}

	private int idForDocId(int docId, SolrIndexSearcher searcher) {
		try {
			Document doc = searcher.doc(docId, idFieldSet);
			return doc.get(idFieldName).hashCode();  // FIXME: hash is not yet unique enough!!
		} catch (IOException e) {
			throw new SolrException(SolrException.ErrorCode.SERVER_ERROR, e);
		}
	}
}