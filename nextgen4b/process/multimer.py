# Ted Cybulski
# 4/1/16

"""
Implemented to analyze Alex's 6mer dataset. It takes in a list of indices 
to define the sites that make up a motif, and anotherlist of indices that 
define the sites we want to count at. Finds unique motifs, then counts the 
incidence of nucleotides at each of the count sites.
"""

from Bio import SeqIO, Seq, SeqRecord
import pandas as pd
from tqdm import tqdm

import sys, os, argparse
    
def extract_motifs_and_bases(f_name, mot_idxs, ct_idxs, bad_chars=['A','-']):
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
    """
    
    seqs = SeqIO.parse(f_name, 'fasta')
    mot = []
    nts = []
    max_idx = max(max(mot_idxs), max(ct_idxs))
     
    for s in seqs:
        # construct motif for each sequence
        if len(s) > max_idx:
            m = ''.join([s[idx] for idx in mot_idxs])
            
            # if it's acceptable, record the motif and count sites
            if all([c not in m for c in bad_chars]):
                mot.append(m)
                nts.append([s[idx] for idx in ct_idxs])
                
    return mot, nts

############
# Output Generators
############

def gen_mot_counts_df(mot, nts, ct_idxs, letter_order=['C','G','T','A']):
    """
    Generate dataframe listing number of base incorporations for each motif.

    Inputs:
    - mot: list of motifs present in the sample
    - nts: list of incorporations present in the sample
    - ct_idxs: list of sites where the bases in `nts` were taken from
    """
    unique_mots = list(set(mot))
    mot_cts = [mot.count(m) for m in unique_mots]
    
    # Build df
    df = pd.DataFrame({'motif': unique_mots, 'total': mot_cts})
    for i, c_idx in enumerate(ct_idxs):
        site_letters = [l[i] for l in nts] # Letters at each site
        for letter in letter_order:
            # Get desired letter count for each motif
            site_mot_ct = [[site_letters[i] for i in range(len(mot))
                            if mot[i] == m].count(letter) for m in unique_mots]
            df['%s_%i_counts' % (letter, c_idx)] = site_mot_ct
    
    return df
    
def gen_mot_lists(mot, nts, site_idx=0,
                  set1=['C', 'G', 'T'], set2=['A']):
    mots_set1 = []
    mots_set2 = []
    
    for i, m in enumerate(mot):
        if nts[i][site_idx] in set1:
            mots_set1.append(m)
        if nts[i][site_idx] in set2:
            mots_set2.append(m)
    
    return mots_set1, mots_set2

############
# File Generators
############

def output_motif_lists(fname, mot_idxs, ct_idxs, bad_chars=['A','-'],
                       reverse_comp_motifs=False, pad='AA'):
    mot, nts = extract_motifs_and_bases(fname, mot_idxs, ct_idxs,
                                        bad_chars=bad_chars)
    l1, l2 = gen_mot_lists(mot, nts, site_idx=0)
    n1, n2 = [''.join(f.split('.')[:-1]) + s for s in ['_set1.fasta', '_set2.fasta']]
    
    SeqIO.write([SeqRecord.SeqRecord(Seq.Seq(pad + s), id=str(i),
                 description='') for i, s in  enumerate(l1)], n1, 'fasta')
    SeqIO.write([SeqRecord.SeqRecord(Seq.Seq(pad + s), id=str(i),
                 description='') for i, s in  enumerate(l2)], n2, 'fasta')
    
def output_motif_counts(fname, mot_idxs, ct_idxs, bad_chars=['A','-']):
    mot, nts = extract_motifs_and_bases(fname, mot_idxs, ct_idxs,
                                        bad_chars=bad_chars)
    df = gen_mot_counts_df(mot, nts, ct_idxs)
    df.to_csv(''.join(fname.split('.')[:-1])+'_motifs.csv')
    
def output_motif_csv(fname, mot_idxs, ct_idxs, bad_chars=['A','-']):
    mot, nts = extract_motifs_and_bases(fname, mot_idxs, ct_idxs,
                                        bad_chars=bad_chars)
    with open(''.join(fname.split('.')[:-1])+'_mot.csv', 'w') as o_f:
        o_f.write(','.join(['motif']+['site_'+str(ct)
                                     for ct in ct_idxs]) + '\n')
        for m, n in zip(mot, nts):
            o_f.write('%s' % m)
            for base in n:
                o_f.write(',%s' % base)
            o_f.write('\n')
    
############
# Do it.
############

def get_all_fnames(directory='.', suffix='.fa'):
    """
    Find all files in the given directory with a given suffix.
    """
    fnames = [f for f in os.listdir(directory)
                if os.path.isfile(f) and f.endswith(suffix)]
    return fnames


if __name__ == '__main__':
    # Parse stuff
    parser = argparse.ArgumentParser(
        description='Get motifs and errors from all .fa files in directory.')
    parser.add_argument('-M', '--motifsites', nargs='+', type=int, metavar='M',
                        help='Sites to look for motif bases', required=True)
    parser.add_argument('-C', '--countsites', nargs='+', type=int, metavar='C',
                        help='Sites to count bases at', required=True)
    parser.add_argument('-B', '--badchars', nargs='*', type=str, metavar='B',
                        default=['A', '-'],
                        help='Remove motifs with these characters')
    parser.add_argument('-O', '--outmode', choices=['meme', 'counts', 'csv'],
                        default='counts')
    args = parser.parse_args(sys.argv[1:])
    
    # Do work
    found_files = get_all_fnames(suffix='.fa')
    
    for f in tqdm(found_files):
        if args.outmode == 'meme':
            output_motif_lists(f, args.motifsites, args.countsites,
                               bad_chars=args.badchars, pad='AA')
        if args.outmode == 'counts':
            output_motif_counts(f, args.motifsites, args.countsites,
                               bad_chars=args.badchars)
        if args.outmode == 'csv':
            output_motif_csv(f, args.motifsites, args.countsites,
                             bad_chars=args.badchars)