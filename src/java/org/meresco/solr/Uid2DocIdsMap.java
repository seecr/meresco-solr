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
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import org.apache.lucene.search.FieldCache;
import org.apache.solr.common.SolrException;
import org.apache.solr.search.SolrIndexSearcher;


public class Uid2DocIdsMap {
	public int numberOfDocIds = 0;
	public Map<Long, List<Integer>> uid2docIds = new HashMap<Long, List<Integer>>();
	
	public Uid2DocIdsMap(SolrIndexSearcher searcher, final String uidFieldName) {
		try {
			long[] uidFieldValues = FieldCache.DEFAULT.getLongs(searcher.getAtomicReader(), uidFieldName, true);
			for (int docId=0; docId < uidFieldValues.length; docId++) {
				long uid = uidFieldValues[docId];
				if (uid == 0) {
					continue;  // deleted doc... 
				}
				List<Integer> l = uid2docIds.get(uid);
				if (l == null) {
					l = new ArrayList<Integer>();
					uid2docIds.put(uid, l);
				}
				l.add(docId);
				numberOfDocIds++;
			}			
		} catch (IOException e) {
			throw new SolrException(SolrException.ErrorCode.SERVER_ERROR, e);
		} catch (NumberFormatException e) {
			throw new SolrException(SolrException.ErrorCode.BAD_REQUEST, "Field " + uidFieldName + " is unknown or not a long field.");
		}		
	}
}