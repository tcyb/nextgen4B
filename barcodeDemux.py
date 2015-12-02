from Bio import SeqIO
import yaml, sys, gzip
import nextgenfilter as ngf

import logging, time

# Initialize logging
timestr = time.strftime("%Y%m%d-%H%M%S")
logging.basicConfig(filename='bcdemux_'+timestr+'.log',
    level=logging.DEBUG, format='%(asctime)s %(message)s')

def demuxByBarcode(yfname, ffname, fsuffix='R1'):
    logging.info('Started forward sequence demuxing of '+ffname)
    # Load YAML
    yf = open(yfname)
    expt_yaml = yaml.load(yf)
    yf.close()
    logging.info('Loaded YAML file: '+yfname)
    
    outfiles = {}
    experimentList = expt_yaml['experiments'].keys()
    logging.info('Found experiments: '+', '.join(experimentList))
    
    # Generate forward files
    for expt in experimentList:
        logging.info('Started processing experiment '+expt)
        outfilename = expt+'_'+fsuffix+'.fastq.gz'
        bc = expt_yaml['experiments'][expt]['barcode']
        
        outfiles[expt] = outfilename
        
        fastqf = ngf.loadNGSFileToIterator(ffname)
        bciterator = (s for s in fastqf if str(s.seq).startswith(bc))
        of = gzip.open(outfilename,'wb')
        SeqIO.write(bciterator, of, "fastq")
        of.close()
        logging.info('Finished writing sequences from experiment '+expt+' to '+outfilename)
    logging.info('Finished forward-strand demuxing of '+ffname)


def demuxPEByBarcode(yfname, pefname, fsuffix='R1', pesuffix='R2'):
    logging.info('Started paired-end sequence demuxing of '+pefname)
    yf = open(yfname)
    expt_yaml = yaml.load(yf)
    yf.close()
    logging.info('Loaded YAML file: '+yfname)
    
    outfiles = {}
    coordsToExperiment = {}
    experimentList = expt_yaml['experiments'].keys()
    logging.info('Found experiments: '+', '.join(experimentList))
    
    logging.info('Generating forward seq coordinate dictionary')
    # Generate coordinate ID to experiments
    for expt in experimentList:
        outfilename = expt+'_'+fsuffix+'.fastq.gz' # Assumes these things were generated by above code. Should be improved...
        bcf = ngf.loadNGSFileToIterator(outfilename)
        coords = ((ngf.getSeqCoords(s), expt) for s in bcf)
        coordsToExperiment.update(coords)
        logging.info('Processed sequences for experiment '+expt)
    logging.info('Generated forward dictionary, found '+str(len(coordsToExperiment.keys()))+' sequences.')
        
    # Generate paired-end files
    logging.info('Finding experiment for each paired-end sequence.')
    pes = ngf.loadNGSFileToIterator(pefname)
    pe_files = {expt: gzip.open(expt+'_'+pesuffix+'.fastq.gz', 'wb') for expt in experimentList}
    for seq in pes:
        try:
            seq_expt = coordsToExperiment[ngf.getSeqCoords(seq)]
            SeqIO.write(seq, pe_files[seq_expt], 'fastq')
        except:
            pass
    logging.info('Finished experiment-matching for paired-end sequences.')
    logging.info('Finished paired-end strand demuxing for '+pefname)
    

if __name__ == '__main__':
    demuxByBarcode(sys.argv[1], sys.argv[2])
    demuxPEByBarcode(sys.argv[1], sys.argv[3])