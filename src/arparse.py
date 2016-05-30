import collections
import inspect
from multiprocessing import cpu_count
from os.path import dirname, basename
from textwrap import wrap as wraptext
from glob import glob

# Logging
import ardebug
debug = ardebug.init()
import armsgs
msgs = armsgs.get_logger((None, debug, "now", "0.0", 1))


class NestedDict(dict):
    """
    A class to generate nested dicts
    """
    def __getitem__(self, item):
        try:
            return dict.__getitem__(self, item)
        except KeyError:
            value = self[item] = type(self)()
            return value


class BaseArgFlag:
    def __init__(self, defname, savname):
        self._argflag = NestedDict()
        self._defname = defname
        self._afout = open(savname, 'w')
        # self._argflag["run"]["ncpus"] = 1
        # self._argflag["a"]["b"]["c"]["d"]["e"] = 5
        # self._argflag["a"]["b"]["c"]["d"]["f"] = 6
        # self._argflag["a"]["b"]["c"]["next"] = 3
        # self._argflag["a"]["b"]["c"]["s"] = "zing"
        # self._argflag["a"]["b"]["g"]["d"]["e"] = "foo"
        # self._argflag["a"]["h"]["c"]["d"]["e"] = "bar"
        # Load the default settings
        self.load()

    def load(self):
        msgs.info("Loading the default settings")
        lines = open(self._defname, 'r').readlines()
        self.load_lines(lines)
        return

    def load_lines(self, lines):
        for ll in lines:
            if len(ll.strip()) == 0:
                # Nothing on a line
                continue
            elif ll.strip()[0] == '#':
                # A comment line
                continue
            self.set_flag(ll.strip().split())
        return

    def arc_comb_match(self, v):
        # Check that v is allowed
        try:
            v = float(v)
        except ValueError:
            msgs.error("The argument of 'arc comb match' must be of type float")
        # Update argument
        self.update(v)

    def bias_comb_method(self, v):
        # Check that v is allowed
        v = v.lower()
        if v not in ['mean', 'median', 'weightmean']:
            msgs.error("The argument of 'bias comb method' must be one of" + msgs.newline() +
                       "'mean', 'median', 'weightmean'")
        # Update argument
        self.update(v)

    def bias_comb_reject_cosmics(self, v):
        # Check that v is allowed
        try:
            v = float(v)
        except ValueError:
            msgs.error("The argument of 'bias comb reject cosmics' must be of type float")
        # Update argument
        self.update(v)

    def bias_comb_reject_replace(self, v):
        # Check that v is allowed
        v = v.lower()
        if v not in ['min', 'max', 'mean', 'median', 'weightmean', 'maxnonsat']:
            msgs.error("The argument of 'bias comb reject replace' must be one of" + msgs.newline() +
                       "'min', 'max', 'mean', 'median', 'weightmean', 'maxnonsat'")
        # Update argument
        self.update(v)

    def bias_comb_reject_lowhigh(self, v):
        # Check that v is allowed
        v = load_list(v)
        # Update argument
        self.update(v)

    def bias_comb_reject_level(self, v):
        # Check that v is allowed
        v = load_list(v)
        # Update argument
        self.update(v)

    def bias_comb_satpix(self, v):
        # Check that v is allowed
        v = v.lower()
        if v not in ['reject', 'force', 'nothing']:
            msgs.error("The argument of 'bias comb satpix' must be one of" + msgs.newline() +
                       "'reject', 'force', 'nothing'")
        # Update argument
        self.update(v)

    def reduce_badpix(self, v):
        # Check that v is allowed
        if v.lower() == "true":
            v = True
        elif v.lower() == "false":
            v = False
        else:
            msgs.error("The argument of 'reduce badpix' can only be 'True' or 'False'")
        # Update argument
        self.update(v)

    def reduce_calibrate(self, v):
        # Check that v is allowed
        if v.lower() == "true":
            v = True
        elif v.lower() == "false":
            v = False
        else:
            msgs.error("The argument of 'reduce calibrate' can only be 'True' or 'False'")
        # Update argument
        self.update(v)

    def reduce_flatfield_method(self, v):
        # Check that v is allowed
        v = v.lower()
        if v not in ["polyscan"]:
            msgs.error("The argument of 'reduce flatfield method' must be one of" + msgs.newline() +
                       "'polyscan'")
        # Update argument
        self.update(v)

    def reduce_flatfield_params(self, v):
        # Check that v is allowed
        v = load_list(v)
        # Update argument
        self.update(v)

    def reduce_flatfield_perform(self, v):
        # Check that v is allowed
        if v.lower() == "true":
            v = True
        elif v.lower() == "false":
            v = False
        else:
            msgs.error("The argument of 'reduce flatfield perform' can only be 'True' or 'False'")
        # Update argument
        self.update(v)

    def reduce_flatfield_useframe(self, v):
        # Check that v is allowed
        v = v.lower()
        # Update argument
        self.update(v)

    def reduce_nonlinear(self, v):
        # Check that v is allowed
        if v.lower() == "true":
            v = True
        elif v.lower() == "false":
            v = False
        else:
            msgs.error("The argument of 'reduce nonlinear' can only be 'True' or 'False'")
        # Update argument
        self.update(v)

    def reduce_overscan_method(self, v):
        # Check that v is allowed
        v = v.lower()
        if v not in ['polynomial', 'savgol']:
            msgs.error("The argument of 'reduce overscan method' must be one of:" + msgs.newline() +
                       "'polynomial', 'savgol'")
        # Update argument
        self.update(v)

    def reduce_overscan_params(self, v):
        # Check that v is allowed
        v = load_list(v)
        # Update argument
        self.update(v)

    def reduce_pixellocations(self, v):
        # Check that v is allowed
        if v.lower() == "none":
            v = None
        elif v.split(".")[-1] == "fits":
            pass
        elif v.split(".")[-2] == "fits" and v.split(".")[-1] == "gz":
            pass
        else:
            msgs.error("The argument of 'reduce pixellocations' must be 'None' or a fits file")
        # Update argument
        self.update(v)

    def reduce_pixelsize(self, v):
        # Check that v is allowed
        try:
            v = float(v)
        except ValueError:
            msgs.error("The argument of 'reduce pixelsize' must be of type float")
        # Update argument
        self.update(v)

    def reduce_refframe(self, v):
        # Check that v is allowed
        if v.lower() not in ['geocentric', 'heliocentric', 'barycentric']:
            msgs.error("The argument of 'reduce refframe' must be one of:" + msgs.newline() +
                       "'geocentric', 'heliocentric', 'barycentric'")
        # Update argument
        self.update(v)

    def reduce_skysub_perform(self, v):
        # Check that v is allowed
        if v.lower() == "true":
            v = True
        elif v.lower() == "false":
            v = False
        else:
            msgs.error("The argument of 'reduce skysub perform' can only be 'True' or 'False'")
        # Update argument
        self.update(v)

    def reduce_trim(self, v):
        # Check that v is allowed
        if v.lower() == "true":
            v = True
        elif v.lower() == "false":
            v = False
        else:
            msgs.error("The argument of 'reduce trim' can only be 'True' or 'False'")
        # Update argument
        self.update(v)

    def reduce_usebias(self, v):
        # Check that v is allowed
        if v.lower() == "none":
            v = None
        # Update argument
        self.update(v)

    def run_calcheck(self, v):
        # Check that v is allowed
        if v.lower() == "true":
            v = True
        elif v.lower() == "false":
            v = False
        else:
            msgs.error("The argument of 'run calcheck' can only be 'True' or 'False'")
        # Update argument
        self.update(v)

    def run_directory_master(self, v):
        # Check that v is allowed

        # Update argument
        self.update(v)

    def run_directory_plots(self, v):
        # Check that v is allowed

        # Update argument
        self.update(v)

    def run_directory_science(self, v):
        # Check that v is allowed

        # Update argument
        self.update(v)

    def run_ncpus(self, v):
        # Check that v is allowed
        curcpu = self._argflag['run']['ncpus']
        cpucnt = cpu_count()
        if v == 'all':
            v = cpucnt  # Use all available cpus
            if v != curcpu:
                msgs.info("Setting {0:d} CPUs".format(v))
        elif v is None:
            v = cpucnt-1  # Use all but 1 available cpus
            if v != curcpu:
                msgs.info("Setting {0:d} CPUs".format(v))
        else:
            try:
                v = int(v)
                if v > cpucnt:
                    msgs.warn("You don't have {0:d} CPUs!".format(v))
                    v = cpucnt
                elif v < 0:
                    v += cpucnt
                if v != curcpu:
                    msgs.info("Setting {0:d} CPUs".format(v))
            except ValueError:
                msgs.error("Incorrect argument given for number of CPUs" + msgs.newline() +
                           "Please choose from -" + msgs.newline() +
                           "all, 1..."+str(cpucnt))
                if cpucnt == 1:
                    if cpucnt != curcpu:
                        msgs.info("Setting 1 CPU")
                    v = 1
                else:
                    v = cpu_count()-1
                    if v != curcpu:
                        msgs.info("Setting {0:d} CPUs".format(v))
        # Update argument
        self.update(v)

    def run_preponly(self, v):
        # Check that v is allowed
        if v.lower() == "true":
            v = True
        elif v.lower() == "false":
            v = False
        else:
            msgs.error("The argument of 'run preponly' can only be 'True' or 'False'")
        # Update argument
        self.update(v)

    def run_qcontrol(self, v):
        # Check that v is allowed
        if v.lower() == "true":
            v = True
        elif v.lower() == "false":
            v = False
        else:
            msgs.error("The argument of 'run qcontrol' can only be 'True' or 'False'")
        # Update argument
        self.update(v)

    def run_spectrograph(self, v):
        # Check that v is allowed
        stgs_arm = glob(dirname(__file__)+"/settings.arm*")
        stgs_all = glob(dirname(__file__)+"/settings.*")
        stgs_spc = list(set(stgs_arm) ^ set(stgs_all))
        spclist = [basename(stgs_spc[0]).split(".")[-1].lower()]
        for i in xrange(1, len(stgs_spc)):
            spclist += [basename(stgs_spc[i]).split(".")[-1].lower()]
        # Check there are no duplicate names
        if len(spclist) != len(set(spclist)):
            msgs.bug("Duplicate settings files found")
            msgs.error("Cannot continue with an ambiguous settings file")
        # Check the settings file exists
        if v.lower() not in spclist:
            msgs.error("Settings do not exist for the {0:s} spectrograph".format(v.lower()) + msgs.newline() +
                       "Please use one of the following spectrograph settings:" + msgs.newline() +
                       wraptext(", ".join(spclist), width=60))
        # Update argument
        self.update(v)

    def run_stopcheck(self, v):
        # Check that v is allowed
        if v.lower() == "true":
            v = True
        elif v.lower() == "false":
            v = False
        else:
            msgs.error("The argument of 'run stopcheck' can only be 'True' or 'False'")
        # Update argument
        self.update(v)

    def run_useIDname(self, v):
        # Check that v is allowed
        if v.lower() == "true":
            v = True
        elif v.lower() == "false":
            v = False
        else:
            msgs.error("The argument of 'run useIDname' can only be 'True' or 'False'")
        # Update argument
        self.update(v)

    def save(self):
        """
        Save the settings used for this reduction
        """
        def savedict(dct):
            for key, value in dct.iteritems():
                self._afout.write(str(key))
                if isinstance(value, dict):
                    savedict(value)
                else:
                    self._afout.write(" " + str(value) + "\n")
        savedict(self._argflag.copy())
        self._afout.close()
        return

    def set_flag(self, lst):
        cnt = 1
        func = None
        succeed = False
        while cnt < len(lst):
            try:
                func = "self." + "_".join(lst[:-cnt]) + "({0:s})".format(" ".join(lst[-cnt:]))
                eval(func)
                succeed = True
            except:
                cnt += 1
                continue
        if not succeed:
            msgs.error("There appears to be an error on the following input line:" + msgs.newline() +
                       " ".join(lst))
        return

    def update(self, v, ll=None):
        """
        Update an element in argflag
        """
        def ingest(dct, upd):
            """
            Ingest the upd dictionary into dct
            """
            for kk, vv in upd.iteritems():
                if isinstance(vv, collections.Mapping):
                    r = ingest(dct.get(kk, {}), vv)
                    dct[kk] = r
                else:
                    dct[kk] = upd[kk]
            return dct
        # First derive a list of the arguments for the keyword to be updated
        if ll is None:
            # update() is called from within this class,
            # so grab the name of the parent function
            ll = inspect.currentframe().f_back.f_code.co_name.split('_')
        # Store a copy of the dictionary to be updated
        dstr = self._argflag.copy()
        # Formulate a dictionary that lists the argument to be updated
        udct = dict({ll[-1]: v})
        for ii in xrange(1, len(ll)):
            udct = dict({ll[-ii-1]: udct.copy()})
        # Update the master dictionary
        self._argflag = ingest(dstr, udct).copy()
        return


class BaseSpect:
    def __init__(self):
        self._spect = NestedDict()

    def mosaic_ndet(self, v):
        # Check that v is allowed

        # Update argument
        self.update(v)

    def set_spect(self, lst):
        func = "self." + "_".join(lst[:-1]) + "({0:s})".format(lst[-1])
        eval(func)


class ARMLSD(BaseArgFlag):
    def reduce_flexure_maxshift(self, v):
        # Check that v is allowed
        try:
            v = int(v)
        except ValueError:
            msgs.error("The argument of 'reduce flexure maxshift' must be of type int")
        # Update argument
        self.update(v)

    def reduce_flexure_spec(self, v):
        # Check that v is allowed
        v = v.lower()
        if v == "none":
            v = None
        elif v in ['boxcar', 'slit_cen']:
            pass
        else:
            msgs.error("The argument of 'reduce flexure spec' must be one of:" + msgs.newline() +
                       "'boxcar', 'slit_cen'")
        # Update argument
        self.update(v)

    def reduce_fluxcal_perform(self, v):
        # Check that v is allowed
        if v.lower() == "true":
            v = True
        elif v.lower() == "false":
            v = False
        else:
            msgs.error("The argument of 'reduce fluxcal perform' can only be 'True' or 'False'")
        # Update argument
        self.update(v)


def get_argflag(init=None):
    """
    Get the Arguments and Flags
    ----------
    init : tuple
      For instantiation

    Returns
    -------
    argflag : Arguments and Flags
    """
    global pypit_argflag

    # Instantiate??
    if init is not None:
        try:
            pypit_argflag = eval(init+"()")
        except RuntimeError:
            msgs.error("Reduction type '{0:s}' is not allowed".format(init))

    return pypit_argflag


def get_spect(init=None):
    """
    Get the Arguments and Flags
    ----------
    init : tuple
      For instantiation

    Returns
    -------
    argflag : Arguments and Flags
    """
    global pypit_spect

    # Instantiate??
    if init is not None:
        if init == "ARMLSD":
            pypit_spect = ARMLSD_spect()

    return pypit_spect


def load_list(strlist):
    temp = strlist.lstrip('([').rstrip(')]').split(',')
    addarr = []
    # Find the type of the array elements
    for i in temp:
        if i.lower() == 'none':
            # None type
            addarr += [None]
        elif i.lower() == 'true' or i.lower() == 'false':
            # bool type
            addarr += [i.lower() in ['true']]
        elif ',' in i:
            # a list
            addarr += i.lstrip('([').rstrip('])').split(',')
            msgs.bug("nested lists could cause trouble if elements are not strings!")
        elif '.' in i:
            try:
                # Might be a float
                addarr += [float(i)]
            except ValueError:
                # Must be a string
                addarr += [i]
        else:
            try:
                # Could be an integer
                addarr += [int(i)]
            except ValueError:
                # Must be a string
                addarr += [i]
    return addarr

"""
af = get_argflag("ARMLSD")
af.set_flag(["run", "ncpus", "5"])
af.set_flag(["a", "b", "c", "d", "e", "47"])
pdb.set_trace()
"""
