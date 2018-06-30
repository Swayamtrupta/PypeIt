""" Class for guiding calibration object generation in PYPIT
"""
from __future__ import absolute_import, division, print_function

import inspect
import numpy as np
import os


from pypit import msgs
from pypit import ardebug as debugger
from pypit import arpixels

from pypit.core import arsort
from pypit.core import armasters

from pypit import arcimage
from pypit import biasframe
from pypit.spectrographs import bpmimage
from pypit import flatfield
from pypit import traceimage
from pypit import traceslits
from pypit import wavecalib
from pypit import wavetilts


# For out of PYPIT running
if msgs._debug is None:
    debug = debugger.init()
    debug['develop'] = True
    msgs.reset(debug=debug, verbosity=2)

# Does not need to be global, but I prefer it
frametype = 'bias'

# Place these here or elsewhere?
#  Wherever they be, they need to be defined, described, etc.
#  These are settings beyond those in the Parent class (ProcessImages)
additional_default_settings = {frametype: {'useframe': 'none'}}


class Calibrations(object):
    """
    This class is primarily designed to guide the generation of calibration images
    and objects in PYPIT

    Parameters
    ----------

    Attributes
    ----------

    Inherited Attributes
    --------------------
    """
    def __init__(self, fitstbl):

        # Parameters unique to this Object
        self.fitstbl = fitstbl

        # Set spectrograph from FITS table
        self.spectrograph = self.fitstbl['instrume'][0]

        # Attributes
        self.calib_dict = {}
        self.det = None
        self.sci_ID = None
        self.settings = None
        self.setup = None

        # Internals
        self.msarc = None
        self.msbias = None
        self.mbpm = None
        self.pixlocn = None
        self.tslits_dict = None
        self.maskslits = None
        self.wavecalib = None

    def set(self, setup, det, sci_ID, settings):
        self.setup = setup
        self.det = det
        self.sci_ID = sci_ID
        self.settings = settings.copy()
        # Setup the calib_dict
        if self.setup not in self.calib_dict.keys():
            self.calib_dict[self.setup] = {}

        # Reset internals to None
        msgs.work("Reset all the internals to None")

    def get_arc(self, bias=None):
        # Checks
        if bias is not None:
            self.msbias = bias
        if self.msbias is None:
            msgs.error("msbias needs to be set prior to arc")
        # Check
        self._chk_set(['setup', 'det', 'sci_ID', 'settings'])
        #
        if 'arc' in self.calib_dict[self.setup].keys():
            self.msarc = self.calib_dict[self.setup]['arc']
        else:
            # Instantiate with everything needed to generate the image (in case we do)
            self.arcImage = arcimage.ArcImage([], spectrograph=self.fitstbl['instrume'][0],
                                settings=self.settings, det=self.det, setup=self.setup,
                                sci_ID=self.sci_ID, msbias=self.msbias, fitstbl=self.fitstbl)
            # Load the MasterFrame (if it exists and is desired)?
            self.msarc = self.arcImage.master()
            if self.msarc is None:  # Otherwise build it
                msgs.info("Preparing a master {0:s} frame".format(self.arcImage.frametype))
                self.msarc = self.arcImage.build_image()
                # Save to Masters
                self.arcImage.save_master(self.msarc, raw_files=self.arcImage.file_list, steps=self.arcImage.steps)
            # Return
            return self.msarc
            '''
            # Grab it -- msarc will be a 2D image
            self.msarc, self.arcImage = arcimage.get_msarc(self.det, self.setup, self.sci_ID,
                                          self.fitstbl, self.settings, self.msbias)
            '''
            # Save
            self.calib_dict[self.setup]['arc'] = self.msarc
        # Return
        return self.msarc

    def get_bias(self):
        # Checks
        self._chk_set(['setup', 'det', 'sci_ID', 'settings'])
        #
        if 'bias' in self.calib_dict[self.setup].keys():
            self.msbias = self.calib_dict[self.setup]['bias']
        else:
            # Init
            self.biasFrame = biasframe.BiasFrame(settings=self.settings, setup=self.setup,
                                  det=self.det, fitstbl=self.fitstbl, sci_ID=self.sci_ID)
            # Load the MasterFrame (if it exists and is desired) or the command (e.g. 'overscan')
            msbias = self.biasFrame.master()
            if msbias is None:  # Build it and save it
                msbias = self.biasFrame.build_image()
                self.biasFrame.save_master(msbias, raw_files=self.biasFrame.file_list,
                                      steps=self.biasFrame.steps)
            # Return
            return msbias#, biasFrame
            '''
            # Grab it
            #   Bias will either be an image (ndarray) or a command (str, e.g. 'overscan') or none
            self.msbias, self.biasFrame = biasframe.get_msbias(
                self.det, self.setup, self.sci_ID, self.fitstbl, self.settings)
            # Save
            self.calib_dict[self.setup]['bias'] = self.msbias
            '''
        # Return
        return self.msbias

    def get_bpm(self, arc=None, bias=None):
        if arc is not None:
            self.msarc = arc
        if bias is not None:
            self.msbias = bias
        # Check me
        self._chk_set(['det', 'settings', 'sci_ID'])
        ###############################################################################
        # Generate a bad pixel mask (should not repeat)
        if 'bpm' in self.calib_dict[self.setup].keys():
            self.msbpm = self.calib_dict[self.setup]['bpm']
        else:
            scidx = np.where((self.fitstbl['sci_ID'] == self.sci_ID) & self.fitstbl['science'])[0][0]
            bpmImage = bpmimage.BPMImage(spectrograph=self.spectrograph,
                            settings=self.settings, det=self.det,
                            shape=self.msarc.shape,
                            binning=self.fitstbl['binning'][scidx],
                            reduce_badpix=self.settings['reduce']['badpix'],
                            msbias=self.msbias)
            self.msbpm = bpmImage.build()
            '''
            # Grab it -- msbpm is a 2D image
            scidx = np.where((self.fitstbl['sci_ID'] == self.sci_ID) & self.fitstbl['science'])[0][0]
            self.msbpm, _ = bpmimage.get_mspbm(self.det, self.fitstbl['instrume'][0],
                                          self.settings, self.msarc.shape,
                                          binning=self.fitstbl['binning'][scidx],
                                          reduce_badpix=self.settings['reduce']['badpix'],
                                          msbias=self.msbias)
            '''
            # Save
            self.calib_dict[self.setup]['bpm'] = self.msbpm
        # Return
        return self.msbpm

    def get_pixflatnrm(self, datasec_img):
        if self.settings['reduce']['flatfield']['perform']:  # Only do it if the user wants to flat field
            # Checks
            if not self._chk_objs(['tslits_dict', 'mstilts']):
                return
            self._chk_set(['det', 'settings', 'sci_ID', 'setup'])
            #
            if 'normpixelflat' in self.calib_dict[self.setup].keys():
                self.mspixflatnrm = self.calib_dict[self.setup]['normpixelflat']
                self.slitprof = self.calib_dict[self.setup]['slitprof']
            else:
                # Settings kludge
                # TODO -- Redo this in the settings refactor
                flat_settings = dict(flatfield=self.settings['reduce']['flatfield'].copy(),
                                     slitprofile=self.settings['reduce']['slitprofile'].copy(),
                                     combine=self.settings['pixelflat']['combine'].copy(),
                                     masters=self.settings['masters'].copy(),
                                     detector=self.settings['detector'])
                # Instantiate
                pixflat_image_files = arsort.list_of_files(self.fitstbl, 'pixelflat', self.sci_ID)
                self.flatField = flatfield.FlatField(file_list=pixflat_image_files, msbias=self.msbias,
                                      spectrograph=self.spectrograph,
                                      settings=flat_settings,
                                      tslits_dict=self.tslits_dict,
                                      tilts=self.mstilts, det=self.det, setup=self.setup,
                                      datasec_img=datasec_img)

                # Load from disk (MasterFrame)?
                self.mspixflatnrm = self.flatField.master()
                self.slitprof = None
                # Load user supplied flat (e.g. LRISb with pixel flat)?
                if flat_settings['flatfield']['useframe'] not in ['pixelflat', 'trace']:
                    mspixelflat_name = armasters.user_master_name(flat_settings['masters']['directory'],
                                                                  flat_settings['flatfield']['useframe'])
                    self.mspixflatnrm, head, _ = armasters._load(mspixelflat_name, exten=self.det, frametype=None, force=True)
                    # TODO -- Handle slitprof properly, i.e.g from a slit flat for LRISb
                    self.slitprof = np.ones_like(self.mspixflatnrm)
                if self.mspixflatnrm is None:
                    # TODO -- Consider turning the following back on.  I'm regenerating the flat for now
                    # Use mstrace if the indices are identical
                    #if np.all(arsort.ftype_indices(fitstbl,'trace',1) ==
                    #                  arsort.ftype_indices(fitstbl, 'pixelflat', 1)) and (traceSlits.mstrace is not None):
                    #    flatField.mspixelflat = traceSlits.mstrace.copy()
                    # Run
                    self.mspixflatnrm, self.slitprof = self.flatField.run(armed=False)
                    # Save to Masters
                    self.flatField.save_master(self.mspixflatnrm, raw_files=pixflat_image_files, steps=self.flatField.steps)
                    self.flatField.save_master(self.slitprof, raw_files=pixflat_image_files, steps=self.flatField.steps,
                                          outfile=armasters.master_name('slitprof', self.setup, flat_settings['masters']['directory']))
                else:
                    if self.slitprof is None:
                        self.slitprof, _, _ = self.flatField.load_master_slitprofile()
                # Save internallly
                self.calib_dict[self.setup]['normpixelflat'] = self.mspixflatnrm
                self.calib_dict[self.setup]['slitprof'] = self.slitprof
        else:
            self.mspixflatnrm = None
            self.slitprof = None

        # Return
        return self.mspixflatnrm, self.slitprof

    def get_slits(self, datasec_img):
        if not self._chk_objs(['pixlocn']):
            return
        # Check me
        self._chk_set(['det', 'settings', 'setup', 'sci_ID'])
        #
        if 'trace' in self.calib_dict[self.setup].keys():  # Internal
            self.tslits_dict = self.calib_dict[self.setup]['trace']
        else:
            '''
            # Setup up the settings (will be Refactored with settings)
            # Get it -- Key arrays are in the tslits_dict
            tslits_dict, _ = traceslits.get_tslits_dict(
                det, setup, spectrograph, sci_ID, ts_settings, tsettings, fitstbl, pixlocn,
                msbias, msbpm, datasec_img, trim=settings.argflag['reduce']['trim'])
            '''
            # Instantiate (without mstrace)
            self.traceSlits = traceslits.TraceSlits(None, self.pixlocn, settings=self.settings,
                                    det=self.det, setup=self.setup, binbpx=self.msbpm)

            # Load via master, as desired
            if not self.traceSlits.master():
                # Build the trace image first
                trace_image_files = arsort.list_of_files(self.fitstbl, 'trace', self.sci_ID)
                Timage = traceimage.TraceImage(trace_image_files,
                                               spectrograph=self.spectrograph,
                                               settings=self.settings, det=self.det,
                                               datasec_img=datasec_img)
                mstrace = Timage.process(bias_subtract=self.msbias, trim=self.settings['reduce']['trim'],
                                         apply_gain=True)

                # Load up and get ready
                self.traceSlits.mstrace = mstrace
                _ = self.traceSlits.make_binarr()
                # Now we go forth
                self.traceSlits.run(arms=True)
                # QA
                self.traceSlits._qa()
                # Save to disk
                self.traceSlits.save_master()

            # Dict
            self.tslits_dict = self.traceSlits._fill_tslits_dict()
            # Save in calib
            self.calib_dict[self.setup]['trace'] = self.tslits_dict

        ###############################################################################
        # Initialize maskslits
        nslits = self.tslits_dict['lcen'].shape[1]
        self.maskslits = np.zeros(nslits, dtype=bool)

        # Return
        return self.tslits_dict, self.maskslits

    def get_wv_calib(self, arc=None):
        if arc is not None:
            self.msarc = arc
        # Checks
        if not self._chk_objs(['msarc','tslits_dict','pixlocn']):
            return
        self._chk_set(['det', 'settings', 'setup', 'sci_ID'])
        ###############################################################################
        if 'wavecalib' in self.calib_dict[self.setup].keys():
            self.wv_calib = self.calib_dict[self.setup]['wavecalib']
            self.wv_maskslits = self.calib_dict[self.setup]['wvmask']
        elif self.settings["reduce"]["calibrate"]["wavelength"] == "pixel":
            msgs.info("A wavelength calibration will not be performed")
            self.wv_calib = None
            self.wv_maskslits = np.zeros_like(self.maskslits, dtype=bool)
        else:
            # Setup up the settings
            # TODO (Refactor with new settings)
            nonlinear = self.settings['detector']['saturation'] * self.settings['detector']['nonlinear']
            self.settings['calibrate'] = self.settings['arc']['calibrate']
            # Instantiate
            self.waveCalib = wavecalib.WaveCalib(self.msarc, spectrograph=self.spectrograph,
                                  settings=self.settings, det=self.det,
                                  setup=self.setup, fitstbl=self.fitstbl, sci_ID=self.sci_ID)
            # Load from disk (MasterFrame)?
            self.wv_calib = self.waveCalib.master()
            # Build?
            if self.wv_calib is None:
                self.wv_calib, _ = self.waveCalib.run(self.tslits_dict['lcen'], self.tslits_dict['rcen'],
                                            self.pixlocn, nonlinear=nonlinear)
                # Save to Masters
                self.waveCalib.save_master(self.waveCalib.wv_calib)
            else:
                self.waveCalib.wv_calib = self.wv_calib
            # Mask
            self.wv_maskslits = self.waveCalib._make_maskslits(self.tslits_dict['lcen'].shape[1])

            # Save in calib
            self.calib_dict[self.setup]['wavecalib'] = self.wv_calib
            self.calib_dict[self.setup]['wvmask'] = self.wv_maskslits
        # Mask me
        self.maskslits += self.wv_maskslits

        # Return
        return self.wv_calib, self.maskslits


    def get_pixlocn(self, arc=None):
        if arc is not None:
            self.msarc = arc
        # Check
        self._chk_set(['settings'])
        #
        xgap = self.settings['detector']['xgap']
        ygap = self.settings['detector']['ygap']
        ysize = self.settings['detector']['ysize']
        self.pixlocn = arpixels.core_gen_pixloc(self.msarc.shape, xgap=xgap, ygap=ygap, ysize=ysize)
        # Return
        return self.pixlocn

    def get_tilts(self, arc=None, ):
        # Checks
        if not self._chk_objs(['msarc','tslits_dict','pixlocn','wv_calib','maskslits']):
            return
        self._chk_set(['det', 'settings', 'setup', 'sci_ID'])
        #
        if 'tilts' in self.calib_dict[self.setup].keys():
            self.mstilts = self.calib_dict[self.setup]['tilts']
            self.wt_maskslits = self.calib_dict[self.setup]['wtmask']
        else:
            # Settings kludges
            tilt_settings = dict(tilts=self.settings['trace']['slits']['tilts'].copy())
            tilt_settings['tilts']['function'] = self.settings['trace']['slits']['function']
            self.settings['tilts'] = tilt_settings['tilts'].copy()
            # Instantiate
            self.waveTilts = wavetilts.WaveTilts(self.msarc, settings=self.settings,
                                  det=self.det, setup=self.setup,
                                  tslits_dict=self.tslits_dict, settings_det=self.settings['detector'],
                                  pixlocn=self.pixlocn)
            # Master
            self.mstilts = self.waveTilts.master()
            if self.mstilts is None:
                self.mstilts, self.wt_maskslits = self.waveTilts.run(maskslits=self.maskslits,
                                                      wv_calib=self.wv_calib)
                self.waveTilts.save_master()
            else:
                self.wt_maskslits = np.zeros_like(self.maskslits, dtype=bool)
            # Save
            self.calib_dict[self.setup]['tilts'] = self.mstilts
            self.calib_dict[self.setup]['wtmask'] = self.wt_maskslits

        # Mask me
        self.maskslits += self.wt_maskslits

        # Return
        return self.mstilts, self.maskslits

    def _chk_set(self, items):
        for item in items:
            if getattr(self, item) is None:
                msgs.error("Use self.set to specify '{:s}' prior to generating the bias".format(item))

    def _chk_objs(self, items):
        for obj in items:
            if getattr(self, obj) is None:
                msgs.warn("You need to generate {:s} prior to wavelength calibration..".format(obj))
                if obj in ['tslits_dict','maskslits']:
                    msgs.warn("Use get_slits".format(obj))
                else:
                    # Strip ms
                    if obj[0:2] == 'ms':
                        iobj = obj[2:]
                    else:
                        iobj = obj
                    msgs.warn("Use get_{:s}".format(iobj))
                return False
        return True


    def full_calibrate(self):
        self.msbias = self.get_bias()
        self.msarc = self.get_arc(self.msbias)
        self.msbpm = self.get_bpm(self.msarc, self.msbias)
        self.pixlocn = self.make_pixlocn(self.msarc)
