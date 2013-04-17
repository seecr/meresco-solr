package org.meresco.solr;

import java.util.HashMap;

import org.apache.commons.lang.NotImplementedException;
import org.apache.lucene.search.Filter;
import org.apache.lucene.util.OpenBitSet;
import org.apache.solr.search.DocIterator;
import org.apache.solr.search.DocSet;

class JoinDocSet implements DocSet {
	private DocSet docSet;
	private HashMap<String, DocSet> otherCoreDocSets;

	public JoinDocSet(DocSet docSet, HashMap<String, DocSet> otherCoreDocSets) {
		this.docSet = docSet;
		this.otherCoreDocSets = otherCoreDocSets;
	}
	
	public DocSet getOtherCoreDocSet(String core) {
		return otherCoreDocSets.get(core);
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
