import nitro
import logging, time
log = logging.getLogger(__name__)
from nitro_parts.Cypress import CY7C68013 as fx2
from nitro_parts.Cypress.CY7C68013 import program_fx2, program_fx2_prom

default_di_file = "BrooksEE/UXN1230/UXN1230.xml"
default_VID = 0x1fe1
default_PID = 0x1230

################################################################################
def get_dev(di_file=default_di_file, serial_num=None, bus_addr=None, VID=default_VID, PID=default_PID, timeout=10):
    """Opens a device and loads the DI file. If a serial_num is
       provided, this opens that device. You can also specify the VID
       and PID. This will wait until 'timeout' seconds for a device to
       connect."""

    dev=fx2.get_dev(di_file=di_file, serial_num=serial_num, bus_addr=bus_addr, VID=VID, PID=PID, timeout=timeout)
    return UXN1230(dev)


################################################################################
def init_dev(dev, di_file=default_di_file):
    """Initializes the device with the di files."""

    fx2.init_dev(dev,di_file)


################################################################################
def program_new_pcb(fx2_firmware, fpga_firmware, VID=default_VID, PID=default_PID, di_file=default_di_file):
    """
        This function does not require an open device.  It looks
        for the 1st unprogrammed pcb (by using the default Cypress
        Vendor ID/Product ID and attempts to load the fx2 firmware
        and fpga firmware files specified.

        :param fx2_firmware: The fx2 firmare ihx file. 
        :param fpga_firmware: The FPGA prom file for spi flash.
    """
    fx2.program_new_pcb(fx2_firmware, VID=VID, PID=PID, di_file=di_file)

################################################################################
class UXN1230(nitro.DevBase):

    ###################### FPGA methods ########################################
    def reboot_fpga(self):
        """Reboots the FPGA from its PROM"""
        log.info("Booting FPGA from SPI prom")
        self.set("FPGA_CTRL", "boot_fpga", 1);
        time.sleep(.2)
        if not(self.is_fpga_programmed()):
            raise Exception("The FPGA did not boot correctly.")

    def program_fpga(self, filename):
        """Programs the FPGA with the provided bitfile"""
        log.info("Programming FPGA with %s" % filename)
        self.write("PROGRAM_FPGA", 0, open(filename, 'rb').read(), 10000)
        if not self.is_fpga_programmed(): 
            raise Exception("The FPGA did not program." ) 
        log.info("Programming succeeded")

    def program_prom(self,filename):
        fx2.program_fx2_prom(self,filename,'FX2_PROM')

    def program_fpga_prom(self, filename):
        """Reprograms spi flash with new prom file.  Forces a reboot the FPGA to run this bitfile when it is complete"""
        from nitro_parts.Numonyx import M25P
        self.set("FX2_SFR", "IOA.prog_b", 0) # reset FPGA
        M25P.program(self, filename, "FPGA_PROM", "FPGA_PROM_CTRL")
        self.reboot_fpga()
    
    def is_fpga_programmed(self):
        """Returns true if the FPGA is programmed and running a valid bitfile."""
        return bool(self.get("FX2_SFR", "IOA.done"))
