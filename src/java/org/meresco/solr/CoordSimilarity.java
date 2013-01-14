package org.meresco.solr;

import org.apache.lucene.search.similarities.DefaultSimilarity;
import org.apache.lucene.index.FieldInvertState;
import org.apache.lucene.index.Norm;

public class CoordSimilarity extends DefaultSimilarity {

    @Override
    public float idf(long docFreq, long numDocs) {
        return 1;
    }

    @Override
    public float queryNorm(float sumOfSquaredWeights) {
        return 1;
    }

    @Override
    public float tf(float freq) {
        return 1;
    }

    @Override
    public float coord(int overlap, int maxOverlap) {
        return 1;
    }
    
    @Override
    public void computeNorm(FieldInvertState state, Norm norm) {

    }
}
