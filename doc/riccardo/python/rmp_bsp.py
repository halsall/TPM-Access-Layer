"""!@package rmp_bsp TPM board support package using RMP access functions
 
This package provides specific functions and procedure to perform read and write accesses
and configure devices hosted on the TPM board, namely ADCs and PLL. These devices are accessed
through an SPI channel using an SPI interface implemented in the FPGA. Accesses to SPI connected 
devices are indirect, these devices are not memory mapped. In order to read/write a register in 
an SPI connected device, it is necessary to instruct the SPI interface inside the FPGA.

FPGA Memory Map\n
Base Address | High Address | Description
-------------|--------------|-------------
0x00010000   | 0x0001FFFF   | JESD Core
0x00020000   | 0x0002FFFF   | SPI Interface
0x00030000   | 0x0003FFFF   | FPGA Registers

JESD Core\n
Refer to Xilinx JESD Core User Guide for detailed registers description\n 

SPI Interface\n
 Offset | Register       | Reset | Mode | Bit |Description
 -------|----------------|-------|------|-----|--------------------------------------------
0x0     | SPI address    | 0x0   | RW   |15:0 | SPI device register address to be accessed
0x4     | SPI write data | 0x0   | RW   |15:8 | write data to SPI device 
0x8     | SPI read data  | 0x0   | RW   |7:0  | read data from SPI device 
0xC     | SPI cmd        | 0x0   | SC   |0    | start SPI access 
-       | -              | 0x0   | RW   |1    | read_not_write bit 
-       | -              | 0x0   | RW   |15:8 | SPI chip select index

FPGA Registers\n
Offset | Register       | Reset | Mode | Bit |Description
-------|----------------|-------|------|-----|--------------------------------------------
0x0    | DATE_CODE_DDHH |  CODE | R    |15:0 | Compile date code 0, format is DDHH
0x4    | DATE_CODE_YYMM |  CODE | R    |15:0 | Compile date code 1, format is YYMM
0x8    | FPGA config    |  0x0  | RW   |0    | dut_rst_ad9528 PLL reset
-      | -              |  0x0  | RW   |1    | dut_spi_ad9528 PLL SPI enable 
-      | -              |  0x0  | RW   |2    | Enable the debug pattern download 
-      | -              |  0x0  | RW   |3    | External trigger enable (NOT USED)
0xC    | JESD reset     |  0x0  | RW   |0    | JESD master reset 
0x10   | Ethernet pause |  0x0  | RW   |0    | pause inserted between two consecutive packets in 10 ns steps
"""
import rmp
from struct import *
import numpy as np
import time

board = "none"
pll_out_config = []
TIMEOUT = 2.0

def spi_matrix(device,idx):
   if board == "XTPM":
      spi_adc_en   = np.array([0,1,2,3,0,1,2,3,0,1,2,3,0,1,2,3])
      spi_adc_sclk = np.array([0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3])
      spi_amp_en   = np.array([0,1,2,3,4,5,6,7,0,1,2,3,4,5,6,7,0,1,2,3,4,5,6,7,0,1,2,3,4,5,6,7])
      spi_amp_sclk = np.array([0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3,0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3])
      spi_pll_en   = np.array([0])
      spi_pll_sclk = np.array([0])
      spi_amp_en   += 4 
      spi_amp_sclk += 4 
      spi_pll_en   += (4+8)
      spi_pll_sclk += (4+4)
   else:
      spi_adc_en   = np.array([0,1])
      spi_adc_sclk = np.array([0,0])
      spi_amp_en   = np.array([3,4,5,6])
      spi_amp_sclk = np.array([0,0,0,0])
      spi_pll_en   = np.array([2])
      spi_pll_sclk = np.array([0])

   spi_en_matrix   = {"adc": spi_adc_en,
                      "amp": spi_amp_en,
                      "pll": spi_pll_en}
   spi_sclk_matrix = {"adc": spi_adc_sclk,
                      "amp": spi_amp_sclk,
                      "pll": spi_pll_sclk}   
      
   spi_en = 0
   spi_sclk = 0
   if idx == "all" and device == "adc":
      for x in spi_adc_en:
         spi_en |= (2**x)
      for x in spi_adc_sclk:
         spi_sclk |= (2**x)
   elif idx != "all":
      spi_en   = 2**(spi_en_matrix[device][idx])
      spi_sclk = 2**(spi_sclk_matrix[device][idx])
   else:
      raise "\"all\" can be used for adc only" 
   return spi_en,spi_sclk
   
def pll_out_type():
   global pll_out_config
   if board == "XTPM":
      pll_out_config = ["sysref",
                        "unused",#"clk", #
                        "clk", #"unused",#
                        "unused",
                        "sysref",
                        "unused",
                        "clk_div_4",
                        "unused",
                        "clk_div_4",
                        "sysref",
                        "sysref",
                        "unused",
                        "clk_div_4",
                        "clk_div_4"]
   else:
      pll_out_config = ["clk_div_4",
                        "clk_div_4",
                        "sysref",
                        "clk",
                        "unused",
                        "unused",
                        "unused",
                        "unused",
                        "clk",
                        "sysref",
                        "unused",
                        "unused",
                        "unused",
                        "sysref"]

def init(str):
   global board
   board = str
   pll_out_type()
   print pll_out_config
   
   
def spi_access(op,spi_en,spi_sclk,add,dat):
   """!@brief Access an SPI connected device
   
   This function provide access to an SPI connected device.
   
   @param op  -- str -- "wr" or "rd"
   @param idx -- int -- This parameter selects the active chip select for the current transaction.
              When more then one SPI device share clock and data line, it is necessary to
              specify which device should be addressed.
   @param add -- int -- SPI device address, register offset to be accessed within the SPI device
   @param dat -- int -- Write data for write operations or don't care for read operations
   
   Returns -- int -- read data for read operations or don't care for write operations
   """
   while(True):
      if ((rmp.rd32(0x20000014)&0x1)==0):
         break
   rmp.wr32(0x20000000,add)
   rmp.wr32(0x20000004,dat << 8)
   rmp.wr32(0x20000008,0x0)
   rmp.wr32(0x2000000C,spi_en)
   rmp.wr32(0x20000010,spi_sclk)
   
   if op == "wr":
      rmp.wr32(0x20000014,0x01)
   elif op == "rd":
      rmp.wr32(0x20000014,0x03)
   while(True):
      if ((rmp.rd32(0x20000014)&0x1)==0):
         break
   return (rmp.rd32(0x20000008) & 0xFF)

def wr_pll(add,dat):
   """!@brief Wrapper for PLL write access, SPI idx 0x4"""
   spi_en,spi_sclk = spi_matrix("pll",0)
   return spi_access("wr",spi_en,spi_sclk,add,dat)
def rd_pll(add):
   """!@brief Wrapper for PLL read access, SPI idx 0x4"""
   spi_en,spi_sclk = spi_matrix("pll",0)
   return spi_access("rd",spi_en,spi_sclk,add,0x0)
def wr_adc(idx,add,dat):
   """!@brief Wrapper for ADC write access, SPI idx 0x1 or 0x2"""
   spi_en,spi_sclk = spi_matrix("adc",idx)
   return spi_access("wr",spi_en,spi_sclk,add,dat)
def rd_adc(idx,add):
   """!@brief Wrapper for ADC read access, SPI idx 0x1 or 0x2"""
   spi_en,spi_sclk = spi_matrix("adc",idx)
   return spi_access("rd",spi_en,spi_sclk,add,0x0)
   
def pll_secure_wr(add,dat):
   """!@brief Securely write PLL registers 
   
   This function read a PLL register and performs a write to that register in case
   the read value differs from dat input parameter. In the ADI demo all the PLL write accesses
   are done this way, I don't know if it is really needed or a simple write is enough...
   
   @param add -- int -- PLL register offset to be accessed
   @param dat -- int -- Write data
   """
   #if rd_pll(add) != dat:
   wr_pll(add,dat)

def pll_out_set(idx):
   type = pll_out_config[idx]
   if type == "clk":
      reg0 = 0x0;
      reg1 = 0x0;
      reg2 = 0x0;
   elif type == "clk_div_4":
      reg0 = 0x0;
      reg1 = 0x0;
      reg2 = 0x3;
   elif type == "sysref":
      reg0 = 0x40;
      reg1 = 0x0;
      reg2 = 0x0;
   else:
      reg0 = 0x0;
      reg1 = 0x0;
      reg2 = 0x0;
   return reg0,reg1,reg2   
   
   
def pll_start(freq):
   """!@brief This function performs the PLL initialization procedure as implemented in ADI demo.

   @param freq -- int -- PLL output frequency in MHz. Supported frequency are 700,800,1000 MHz
   """
   print "Setting PLL. Frequency is " + str(freq)
   if freq != 1000 and freq != 800 and freq != 700:
      print "Frequency " + str(freq) + " MHz is not currently supported."
      print "Switching to default frequency 700 MHz"
      freq = 700

   wr_pll(0x0,0x1)
   while(True):
      if rd_pll(0x0)&0x1 == 0:
         break
    
   wr_pll(0xf,0x1);
  
   if board == "XTPM":
      pll_secure_wr(0x100,0x1);
      pll_secure_wr(0x102,0x1);
      pll_secure_wr(0x104,0xA);  #VCXO100MHz
      pll_secure_wr(0x106,0x94); #VCXO100MHz
      pll_secure_wr(0x107,0x13);
      pll_secure_wr(0x108,0x0);  #VCXO100MHz
      pll_secure_wr(0x109,0x4);
   else:
      pll_secure_wr(0x100,0x1);
      pll_secure_wr(0x102,0x1);
      pll_secure_wr(0x104,0x8);
      pll_secure_wr(0x106,0x14);
      pll_secure_wr(0x107,0x13);
      pll_secure_wr(0x108,0x2A);
      pll_secure_wr(0x109,0x4);
   
   # pll_secure_wr(0x100,0x1);
   # pll_secure_wr(0x102,0x1);
   # #pll_secure_wr(0x104,0x8);
   # pll_secure_wr(0x104,0xA);  #VCXO100MHz
   # #pll_secure_wr(0x106,0x14);
   # pll_secure_wr(0x106,0x94); #VCXO100MHz
   # pll_secure_wr(0x107,0x13);
   # #pll_secure_wr(0x108,0x2A);
   # pll_secure_wr(0x108,0x0); #VCXO100MHz
   # pll_secure_wr(0x109,0x4);
   
   if board == "XTPM":
      pll_secure_wr(0x200,0xFF);
      if freq == 1000:
         pll_secure_wr(0x201,10);
         pll_secure_wr(0x202,0x33);
         pll_secure_wr(0x203,0x10);
         pll_secure_wr(0x204,4);       #M1
         pll_secure_wr(0x205,0x2);
         pll_secure_wr(0x207,0x2);     
         pll_secure_wr(0x208,10-1);    #N1
      elif freq == 800:
         pll_secure_wr(0x201,10);
         pll_secure_wr(0x202,0x33);
         pll_secure_wr(0x203,0x10);
         pll_secure_wr(0x204,5);       #M1
         pll_secure_wr(0x205,0x2);
         pll_secure_wr(0x207,0x2);
         pll_secure_wr(0x208,8-1);     #N1
      elif freq == 700:
         pll_secure_wr(0x201,0xC8);
         pll_secure_wr(0x202,0x33);
         pll_secure_wr(0x203,0x10);
         pll_secure_wr(0x204,0x5);     #M1
         pll_secure_wr(0x205,0x2);
         pll_secure_wr(0x207,0x2);
         pll_secure_wr(0x208,7-1);     #N1
      else:
         print "Error PLL frequency not supported" 
   else:
      pll_secure_wr(0x200,0xe6);
      if freq == 1000:
         pll_secure_wr(0x201,0x19);
         pll_secure_wr(0x202,0x13);
         pll_secure_wr(0x203,0x10);
         pll_secure_wr(0x204,0x4); 
         pll_secure_wr(0x205,0x2);
         pll_secure_wr(0x207,0x2);     
         pll_secure_wr(0x208,0x18); 
      elif freq == 800:
         pll_secure_wr(0x201,0x46);
         pll_secure_wr(0x202,0x33);
         pll_secure_wr(0x203,0x10);
         pll_secure_wr(0x204,0x5); 
         pll_secure_wr(0x205,0x2);
         pll_secure_wr(0x207,0x1);
         pll_secure_wr(0x208,0x4); 
      elif freq == 700:
         pll_secure_wr(0x201,0xeb);
         pll_secure_wr(0x202,0x13);
         pll_secure_wr(0x203,0x10);
         pll_secure_wr(0x204,0x5); 
         pll_secure_wr(0x205,0x2);
         pll_secure_wr(0x207,0x4);
         pll_secure_wr(0x208,0x22);
      else:
         print "Error PLL frequency not supported"
      
   print "Setting PLL outputs"
   # pll_secure_wr(0x301,0x0);
   # pll_secure_wr(0x302,0x3);
   # pll_secure_wr(0x303,0x0);
   # pll_secure_wr(0x305,0x3);
   # pll_secure_wr(0x306,0x40);
   # pll_secure_wr(0x307,0x0);
   # pll_secure_wr(0x308,0x0);
   # pll_secure_wr(0x309,0x0);
   # pll_secure_wr(0x30d,0x0);
   # pll_secure_wr(0x313,0x0);
   # pll_secure_wr(0x319,0x0);
   # pll_secure_wr(0x31a,0x0);
   # pll_secure_wr(0x31f,0x0);
   # pll_secure_wr(0x327,0x40);
   for n in range(14):
      reg0,reg1,reg2 = pll_out_set(n)
      pll_secure_wr(0x300+3*n+0,reg0);
      pll_secure_wr(0x300+3*n+1,reg1);
      pll_secure_wr(0x300+3*n+2,reg2);

   print "Setting SYSREF"
   pll_secure_wr(0x400,0x14);
   #pll_secure_wr(0x400,0x00);
   #pll_secure_wr(0x401,0x20);
   #pll_secure_wr(0x402,0x10);
   pll_secure_wr(0x403,0x96);
   print "Disabling unused channels"
   pll_secure_wr(0x500,0x10);
   pd = 0
   for c in range(14):
      if pll_out_config[c] == "unused":
         pd |= 2**c
   #pll_secure_wr(0x501,0xf0);
   pll_secure_wr(0x501,pd&0xFF);
   #pll_secure_wr(0x502,0x1c);
   pll_secure_wr(0x502,(pd&0xFF00)>>8);      
         
   while(True):
      if rd_pll(0xf) == 0:
         break
   wr_pll(0xf,0x1);

   pll_secure_wr(0x203,0x10);

   while(True):
      if rd_pll(0xf) == 0:
         break
   wr_pll(0xf,0x1);

   pll_secure_wr(0x203,0x11);
   while(True):
      if rd_pll(0xf) == 0:
         break
   wr_pll(0xf,0x1);

   wr_pll(0x403,0x97);
   while(True):
      if rd_pll(0xf) == 0:
         break
   wr_pll(0xf,0x1);

   wr_pll(0x32a,0x1);
   while(True):
      if rd_pll(0xf) == 0:
         break
   wr_pll(0xf,0x1);

   wr_pll(0x32a,0x0);
   while(True):
      if rd_pll(0xf) == 0:
         break
   wr_pll(0xf,0x1);

   wr_pll(0x203,0x10);
   wr_pll(0xf,0x1);
   wr_pll(0x203,0x11);
   wr_pll(0xf,0x1);

   print hex(rd_pll(0x509))
   
   while(True):
      if rd_pll(0x509) == 0x8:
         break

   wr_pll(0x403,0x97);
   wr_pll(0xf,0x1);

   wr_pll(0x32A,0x1);
   wr_pll(0xf,0x1);

   wr_pll(0x32A,0x0);
   wr_pll(0xf,0x1);

   while(True):
      if rd_pll(0x508) == 0xF2:
         print "PLL Locked!"
         break

   
def pll_start2(freq):
   """!@brief This function performs the PLL initialization procedure as implemented in ADI demo.

   @param freq -- int -- PLL output frequency in MHz. Supported frequency are 700,800,1000 MHz
   """
   print "Setting PLL. Frequency is " + str(freq)
   if freq != 1000 and freq != 800 and freq != 700:
      print "Frequency " + str(freq) + " MHz is not currently supported."
      print "Switching to default frequency 700 MHz"
      freq = 700

    #assert(fs in [360, 700, 800, 1000])
    #SelectCSB(csb)
    
   fs = freq
    
   # CLOCK WRITES
   wr_pll(0x0000, 0x81)
   wr_pll(0x0100, 0x01)
   wr_pll(0x0102, 0x01)
   wr_pll(0x0104, 0x08)
   wr_pll(0x0106, 0x14)
   wr_pll(0x0107, 0x13)
   wr_pll(0x0108, 0x2A)
   wr_pll(0x0109, 0x04)
   wr_pll(0x0200, 0xE6)

   if (fs == 1000):
      print "Configuring AD9528 for 1000 Msps"
      wr_pll(0x0201, 0x19)
      wr_pll(0x0202, 0x13)
      wr_pll(0x0203, 0x10)
      wr_pll(0x0204, 0x04)
      wr_pll(0x0205, 0x02)
      wr_pll(0x0207, 0x02)
      wr_pll(0x0208, 0x18)
   elif (fs == 800):
      print "Configuring AD9528 for 800 Msps"
      wr_pll(0x0201, 0x46)
      wr_pll(0x0202, 0x33)
      wr_pll(0x0203, 0x10)
      wr_pll(0x0204, 0x05)
      wr_pll(0x0205, 0x02)
      wr_pll(0x0207, 0x01)
      wr_pll(0x0208, 0x04)
   elif (fs == 700):
      print "Configuring AD9528 for 700 Msps"
      wr_pll(0x0201, 0xEB)
      wr_pll(0x0202, 0x13)
      wr_pll(0x0203, 0x10)
      wr_pll(0x0204, 0x05)
      wr_pll(0x0205, 0x02)
      wr_pll(0x0207, 0x04)
      wr_pll(0x0208, 0x22)
   else:
      print "Configuring AD9528 for 360 Msps"
      wr_pll(0x0201, 0x4B)
      wr_pll(0x0202, 0x33)
      wr_pll(0x0203, 0x00)
      wr_pll(0x0204, 0x05)
      wr_pll(0x0205, 0x02)
      wr_pll(0x0207, 0x01)
      wr_pll(0x0208, 0x08)

   if (fs == 360):
      wr_pll(0x0301, 0x00)
      wr_pll(0x0302, 0x07)
      wr_pll(0x0303, 0x00)
      wr_pll(0x0305, 0x07)
      # wr_pll(0x0306, 0x40)
      wr_pll(0x0306, 0x5B)
      wr_pll(0x0307, 0x00)
      wr_pll(0x0308, 0x09)
      wr_pll(0x0309, 0x00)
      wr_pll(0x030B, 0x01)
      wr_pll(0x030D, 0x00)
      wr_pll(0x0313, 0x00)
      wr_pll(0x0319, 0x00)
      wr_pll(0x031A, 0x01)
      wr_pll(0x031D, 0x01)
      wr_pll(0x031F, 0x00)
      wr_pll(0x0327, 0x40)
      wr_pll(0x0329, 0x01)
      wr_pll(0x0400, 0x14)
      wr_pll(0x0403, 0x96)
      wr_pll(0x0500, 0x10)
      wr_pll(0x0501, 0xF0)
      wr_pll(0x0502, 0x1C)
      wr_pll(0x000F, 0x01)
   else:
      wr_pll(0x0301, 0x00)
      wr_pll(0x0302, 0x03)
      wr_pll(0x0303, 0x00)
      wr_pll(0x0305, 0x03)
      # wr_pll(0x0306, 0x40)
      wr_pll(0x0306, 0x5B)
      wr_pll(0x0307, 0x00)
      wr_pll(0x0308, 0x00)
      wr_pll(0x0309, 0x00)
      wr_pll(0x030D, 0x00)
      wr_pll(0x0313, 0x00)
      wr_pll(0x0319, 0x00)
      wr_pll(0x031A, 0x00)
      wr_pll(0x031F, 0x00)
      wr_pll(0x0327, 0x40)
      wr_pll(0x0400, 0x14)
      wr_pll(0x0403, 0x96)
      wr_pll(0x0500, 0x10)
      wr_pll(0x0501, 0xF0)
      wr_pll(0x0502, 0x1C)
      wr_pll(0x000F, 0x01)

   # Calibration
   print "Calibrating AD9528"
   if (fs == 360):
      wr_pll(0x0203, 0x00)
      wr_pll(0x000F, 0x01)
      wr_pll(0x0203, 0x01)
      wr_pll(0x000F, 0x01)
   else:
      wr_pll(0x0203, 0x10)
      wr_pll(0x000F, 0x01)
      wr_pll(0x0203, 0x11)
      wr_pll(0x000F, 0x01)
     

   # Wait for calibration OK status
   t0 = time.time()
   while (True):
      value = (rd_pll(0x509))        
      if ((value & 0b1) == 0x0):
         break
      if (time.time() - t0) > TIMEOUT:
         raise Exception("Timed out waiting on register 0x509")

   print "AD9528 Calibration complete"

   # Configure AD9528 VCO
   wr_pll(0x032A, 0x01)
   wr_pll(0x000F, 0x01)
   wr_pll(0x032A, 0x00)
   wr_pll(0x000F, 0x01)

   print "AD9528 Configuration complete"

   while(True):
      if rd_pll(0x508) == 0xF2:
         print "AD9528 Locked!"
         break

         
def adc_single_start(idx,bit):
   """!brief This function performs the ADC configuration and initialization procedure as implemented in ADI demo.

   @param idx -- int -- ADC SPI index, legal value with ADI FMC are 0x1 and 0x2 
   @param bit -- int -- Sample bit width, supported value are 8,14
   """
   print "Setting ADC " + str(idx) + " @" + str(bit) + " bit"
   if bit != 14 and bit != 8 :
      print "Bit number " + str(bit) + " is not supported."
      print "Switching to 8 bits"
      bit = 8
   
   wr_adc(idx,0x0,0x1);
   
   wr_adc(idx,0x120,0x0);#sysref
   while(True):
      if(rd_adc(idx,0x0)&0x1==0):
         break
   
   wr_adc(idx,0x550,0x00);#test pattern
   wr_adc(idx,0x573,0x00);#test pattern
   
   if (True):#idx == 1:
      wr_adc(idx,0x551,0x11);#test pattern
      wr_adc(idx,0x552,0x22);#test pattern
      wr_adc(idx,0x553,0x33);#test pattern
      wr_adc(idx,0x554,0x44);#test pattern
      wr_adc(idx,0x555,0x55);#test pattern
      wr_adc(idx,0x556,0x66);#test pattern
      wr_adc(idx,0x557,0x77);#test pattern
      wr_adc(idx,0x558,0x88);#test pattern
      
      wr_adc(idx,0x551,0x11);#test pattern
      wr_adc(idx,0x552,0x55);#test pattern
      wr_adc(idx,0x553,0x33);#test pattern
      wr_adc(idx,0x554,0x55);#test pattern
      wr_adc(idx,0x555,0x55);#test pattern
      wr_adc(idx,0x556,0x55);#test pattern
      wr_adc(idx,0x557,0x77);#test pattern
      wr_adc(idx,0x558,0x55);#test pattern
   else:
      wr_adc(idx,0x551,0x00);#test pattern
      wr_adc(idx,0x552,0x11);#test pattern
      wr_adc(idx,0x553,0x22);#test pattern
      wr_adc(idx,0x554,0x33);#test pattern
      wr_adc(idx,0x555,0x44);#test pattern
      wr_adc(idx,0x556,0x55);#test pattern
      wr_adc(idx,0x557,0x66);#test pattern
      wr_adc(idx,0x558,0x77);#test pattern

   wr_adc(idx,0x571,0x15);
   wr_adc(idx,0x572,0x80);  #SYNC CMOS level
   
   print "sync CMOS " + hex(rd_adc(idx,0x572))
   
   wr_adc(idx,0x58b,0x81);
   wr_adc(idx,0x58d,0x1f);
   if bit == 14:
      wr_adc(idx,0x58f,0xF);
      wr_adc(idx,0x590,0x2F);
      wr_adc(idx,0x570,0x88);
      wr_adc(idx,0x58b,0x83);
      wr_adc(idx,0x590,0x2F);
      
      wr_adc(idx,0x5b2,0x00);
      wr_adc(idx,0x5b3,0x01);
      wr_adc(idx,0x5b5,0x02);
      wr_adc(idx,0x5b6,0x03);
   else:
      wr_adc(idx,0x58f,0x7);
      wr_adc(idx,0x590,0x27);
      wr_adc(idx,0x570,0x48);
      #wr_adc(idx,0x570,0x0);
      wr_adc(idx,0x58b,0x81);
      #wr_adc(idx,0x58b,0x03);
      print "0x58b is " + str(rd_adc(idx,0x58b));
      wr_adc(idx,0x590,0x27);

      wr_adc(idx,0x5b2,0x00);
      wr_adc(idx,0x5b3,0x01);
      wr_adc(idx,0x5b5,0x00);
      wr_adc(idx,0x5b6,0x01);
      wr_adc(idx,0x5b0,0xFA);#xTPM unused lane power down
      
   #wr_adc(idx,0x5B2,0x01);#xTPM lane remap
   #wr_adc(idx,0x5B3,0x02);#xTPM lane remap
   #wr_adc(idx,0x5B5,0x01);#xTPM lane remap
   #wr_adc(idx,0x5BF,0xF);#xTPM drive adj
   #wr_adc(idx,0x5C1,0x55);#xTPM deemph
   #wr_adc(idx,0x5C2,0x7);#xTPM deemph
   #wr_adc(idx,0x5C3,0x7);#xTPM deemph
   #wr_adc(idx,0x5C4,0x7);#xTPM deemph
   #wr_adc(idx,0x5C5,0x7);#xTPM deemph
   
   #wr_adc(idx,0x5b0,0xAA);#xTPM unused lane power down
   
   wr_adc(idx,0x571,0x14);
   
   
      
   while(True):                        #PLL locked
      if(rd_adc(idx,0x56f)!=0x80):
         break
   if bit == 14:
      if (rd_adc(idx,0x58b)!=0x83):    #jesd lane number
         print "Number of lane is not correct"
   else:
      if (rd_adc(idx,0x58b)!=0x81):    #jesd lane number
         print "Number of lane is not correct"
   if (rd_adc(idx,0x58c)!=0):          #octets per frame
      print "Number of octets per frame is not correct"
   if (rd_adc(idx,0x58d)!=0x1f):       #frames per multiframe
      print "Number of frame per multiframe is not correct"
   if (rd_adc(idx,0x58e)!=1):          #virtual converters
      print "Number of virtual converters is not correct"
   print "ADC " + str(idx) + " configured!"
   
def adc_start(idx,bit):
   """!@brief Wrapper function performing ADC configuration"

   @param idx -- int -- ADC SPI index, legal value with ADI FMC are 0x1 and 0x2.
                 "all" cycles through 1 and 2.
   @param bit -- int -- Sample bit width, supported value are 8,14
   """
   if board == "XTPM":
      idx_list = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
   else:
      idx_list = [0,1]
  
   if idx == "all":
      for n in idx_list:
         adc_single_start(n,bit)
   else:
      adc_single_start(idx,bit)
      
def jesd_core_start(bit):
   """!@brief This function performs the FPGA internal JESD core configuration and initialization procedure as implemented in ADI demo.

   @param bit -- int -- Sample bit width, supported value are 8,14
   """
   print "Setting JESD core @" + str(bit) + " bit"
   if bit != 14 and bit != 8 :
      print "Bit number " + str(bit) + " is not supported."
      print "Switching to 8 bits"
      bit = 8
   rmp.wr32(0x00010008, 0x1);
   rmp.wr32(0x00010010, 0x0); #sysref
   rmp.wr32(0x0001000C, 0x1); #scrambling
   rmp.wr32(0x00010020, 0x0);
   rmp.wr32(0x00010024, 0x1f);
   if bit == 14:
      rmp.wr32(0x00010028, 0xF);
   else:
      rmp.wr32(0x00010028, 0x3);
   #rmp.wr32(0x00010028, 0x0); #xTPM
   rmp.wr32(0x0001002C, 0x1);
   rmp.wr32(0x00010004, 0x1);
   
def fpga_start():
   """!@brief This function starts the FPGA acquisition and data downloading through 1Gbit Ethernet
   """
   rmp.wr32(0x30000008, 0x0000);
   rmp.wr32(0x3000000C, 0x2000);
   
   rmp.wr32(0x0000000C, 0xFFFE);
   rmp.wr32(0x00000004, 0x80);#xTPM bit_per_sample
   rmp.wr32(0x00000008, 0x0);
   rmp.wr32(0x00000008, 0x1); # Start data transfer
   
   time.sleep(1)
   
   #wr_adc("all",0x572,0x80);  
   wr_adc("all",0x572,0xC0); #Force ILA and user data phase
   
def fpga_stop():
   """!@brief This function stops the FPGA acquisition and data downloading through 1Gbit Ethernet
   """
   rmp.wr32(0x00000008, 0x0);
   
def acq_start(freq,bit):
   """!@brief This function performs the start-up procedure of the whole system. 
   
   It configures PLL, ADCs and FPGA and starts the data download.

   @param freq -- int -- PLL output frequency in MHz. Supported frequency are 700,800,1000 MHz
   @param bit -- int -- Sample bit width, supported value are 8,14
   """
   fpga_stop()
   #Configure PLL
   pll_start(freq)
   #Configure all ADC
   adc_start("all",bit)
   #Configure JESD core
   jesd_core_start(bit)
   #Start download
   fpga_start()
   print "acq_start done!"

   
   
   
   

