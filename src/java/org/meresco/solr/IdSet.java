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
	private Set<Integer> ids = new HashSet<Integer>();
	private Map<Integer, Integer> id2docId = new HashMap<Integer, Integer>();
	private static final Set<String> ID_FIELDS = new HashSet<String>() {{ this.add("__id__"); }};

	public static IdSet idSetFromDocSet(DocSet docSet, SolrIndexSearcher searcher) {
		if (docSet instanceof JoinDocSet) {
			return ((JoinDocSet) docSet).getIdSet();
		}
		IdSet idSet = new IdSet();
		DocIterator iter = docSet.iterator();
		while (iter.hasNext()) {
			int docId = iter.nextDoc();
			idSet.add(IdSet.idForDocId(docId, searcher), docId);
		}
		return idSet;
	}	
	
	public void add(int id, int docId) {
		ids.add(id);
		id2docId.put(id, docId);
	}
	
	public int get(int id) {
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
    		docIds[docs++] = mapping.get(iter.next());
    	}
		return new HashDocSet(docIds, 0, length);
	}

	public DocSet makeDocSet() {
		return makeDocSet(this);
	}

	private static int idForDocId(int docId, SolrIndexSearcher searcher) {
		Document doc = null;
		try {
			doc = searcher.doc(docId, IdSet.ID_FIELDS);
		} catch (IOException e) {
			throw new SolrException(SolrException.ErrorCode.SERVER_ERROR, e);
		}
		return doc.get("__id__").hashCode();
	}
}