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

import java.util.HashMap;

import org.apache.commons.lang.NotImplementedException;
import org.apache.lucene.search.Filter;
import org.apache.lucene.util.OpenBitSet;
import org.apache.solr.search.DocIterator;
import org.apache.solr.search.DocSet;

class JoinDocSet implements DocSet {
	private IdSet idSet;
	private DocSet docSet;
	private HashMap<String, DocSet> otherCoreDocSets;

	public JoinDocSet(IdSet idSet, HashMap<String, DocSet> otherCoreDocSets) {
		this.idSet = idSet;
		this.docSet = idSet.makeDocSet();
		this.otherCoreDocSets = otherCoreDocSets;
	}
	
	public DocSet getOtherCoreDocSet(String core) {
		return otherCoreDocSets.get(core);
	}
	
	public IdSet getIdSet() {
		return idSet;
	}
	
	@Override
	public void add(int doc) {
		throw new NotImplementedException();
	}

	@Override
	public void addUnique(int doc) {
		throw new NotImplementedException();
	}

	@Override
	public int size() {
		return docSet.size();
	}

	@Override
	public boolean exists(int docid) {
		return docSet.exists(docid);
	}

	@Override
	public DocIterator iterator() {
		return docSet.iterator();
	}

	@Override
	public OpenBitSet getBits() {
		return docSet.getBits();
	}

	@Override
	public long memSize() {
		return docSet.memSize();
	}

	@Override
	public DocSet intersection(DocSet other) {
		return docSet.intersection(other);
	}

	@Override
	public int intersectionSize(DocSet other) {
		return docSet.intersectionSize(other);
	}

	@Override
	public boolean intersects(DocSet other) {
		return docSet.intersects(other);
	}

	@Override
	public DocSet union(DocSet other) {
		return docSet.union(other);
	}

	@Override
	public int unionSize(DocSet other) {
		return docSet.unionSize(other);
	}

	@Override
	public DocSet andNot(DocSet other) {
		return docSet.andNot(other);
	}

	@Override
	public int andNotSize(DocSet other) {
		return docSet.andNotSize(other);
	}

	@Override
	public Filter getTopFilter() {
		return docSet.getTopFilter();
	}

	@Override
	public void setBitsOn(OpenBitSet target) {
		throw new NotImplementedException();
	}
}
