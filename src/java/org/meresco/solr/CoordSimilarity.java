package org.meresco.solr;

import org.apache.lucene.search.similarities.DefaultSimilarity;
import org.apache.lucene.index.FieldInvertState;
import org.apache.lucene.index.Norm;

public class CoordSimilarity extends DefaultSimilarity {
    /**
     * All OR clauses count equally.
     */
    @Override
    public float coord(int overlap, int maxOverlap) {
        return 1F / maxOverlap;
    }

    /**
     * IDF (and TF) are turned off by always returning 1
     * As a result, only the coordination factor determines the score.
     * The coordination factor is the ratio of matching OR clauses.
     **/
    @Override
    public float idf(long docFreq, long numDocs) {
        return 1;
    }
    @Override
    public float tf(float freq) {
        return 1;
    }

    /**
     * We want FieldNorm be 1 regardless if a term is the only term of one of many in a field.
     * E.G. in "subject=rain" and "subject=rain hail" rain is of equal importance.
     */
    @Override
    public void computeNorm(FieldInvertState state, Norm norm) {
    }

    /**
     * Ignore queryNorm to establish deterministic scoring
     */
    @Override
    public float queryNorm(float valueForNormalization) {
        return 1;
    }
 }
