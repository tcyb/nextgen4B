# Ted Cybulski
# 4/1/16

"""
Implemented to analyze Alex's 6mer dataset. It takes in a list of indices 
to define the sites that make up a motif, and anotherlist of indices that 
define the sites we want to count at. Finds unique motifs, then counts the 
incidence of nucleotides at each of the count sites.
"""

from Bio import SeqIO

import pandas as pd
import sys
import os
    
def nmer_extract_from_fa(f_name, mot_idxs, ct_idxs,
                         bad_chars=['A','-'], letter_order=['C','G','T','A']):
    """
    Open a .fasta file, extract a given set of bases as a motif 
    and a given set of bases as counted nts.
    
    Arguments:
    f_name          -- The name of the .fasta file to process
    mot_idxs        -- The 0-indexed indices of the letters that make up a 
                        motif, in order
    ct_idxs         -- The 0-indexed indices of the letters to be counted 
                        (for errors, etc.)
    
    Keywords:
    bad_chars       -- Discard motifs that include these characters
    letter_order    -- The letters we're looking for (in order)
    """
    
    seqs = SeqIO.parse(f_name, 'fasta')
    mot = []
    ct_nts = []
     
    for s in seqs:
        # construct motif for each sequence
        m = ''.join([s[idx] for idx in mot_idxs])
        
        # if it's acceptable, record the motif and count sites
        if all([c not in m for c in bad_chars]):
            mot.append(m)
            ct_nts.append([s[idx] for idx in ct_idxs])
    
    unique_mots = list(set(mot))
    
    # Get totals for each of the motifs
    mot_cts = [mot.count(m) for m in unique_mots]
    
    # Build df
    df = pd.DataFrame({'motif': unique_mots, 'total': mot_cts})
    for c_idx, i in zip(ct_idxs, range(len(ct_idxs))):
        site_letters = [l[i] for l in ct_nts] # Letters at each site
        for letter in letter_order:
            # Get desired letter count for each motif
            site_mot_ct = [[site_letters[i] for i in range(len(mot)) \
                            if mot[i] == m].count(letter) for m in unique_mots]
            df['%s_%i_counts' % (letter, c_idx)] = site_mot_ct
    
    return df



if __name__ == '__main__':
    
    
    for f in found_files:
        df = nmer_extract_from_fa(curr_path+f)