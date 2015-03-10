#ifndef BOARD_CLASS
#define BOARD_CLASS

#include "Definitions.hpp"
#include "MemoryMap.hpp"
#include "Protocol.hpp"
#include "Utils.hpp"

#include <string.h>

using namespace std;

// Class representation of a digital board
// This can eventually be sub-classed to add functionality
// specific to a particular board
class Board
{
    public:
        // Board constructor
        Board(const char *ip, unsigned short port);

        // Board destructor
        virtual ~Board() = 0;

    // ---------- Public class functions --------
    public:

        // Clear everything and remove connection
        virtual void disconnect() = 0;

        // Get board status
        virtual STATUS getStatus() = 0;

        // Get register list
        virtual REGISTER_INFO* getRegisterList(unsigned int *num_registers) = 0;

        // Get register value
        virtual VALUES readRegister(DEVICE device, REGISTER reg, uint32_t n) = 0;

        // Set register value
        virtual ERROR writeRegister(DEVICE device, REGISTER reg, uint32_t n, uint32_t *value) = 0;

        // Asynchronously load firmware to FPGA.
        virtual ERROR loadFirmware(DEVICE device, const char* bitstream) = 0;

        // Synchronously load firmware to FPGA
        virtual ERROR loadFirmwareBlocking(DEVICE device, const char* bitstream) = 0;

    // ---------- Protected class functions ---------- 
    protected:
        // Initialise board
     //   virtual ERROR initialiseBoard();

    // ---------- Protected class members ---------- 
    protected:

        unsigned int    id;   // Board identifier
        char            *ip;  // Board IP address
        unsigned short  port; // Port to communicate with board
        unsigned short  num_fpgas;   // Number of FPGAs on board

        Protocol        *protocol;   // Protocol instance to communicate with board

        MemoryMap       *memory_map; // Memory map instance
};

// Board derived class representing a Tile Processing Modules
class TPM: public Board
{
    public:
        // TPM constructor
        TPM(const char *ip, unsigned short port);

        // TPM destructor
        ~TPM();

    public:
        // Clear everything and remove connection
        void disconnect();

        // Get board status
        STATUS getStatus();

        // Get register list
        REGISTER_INFO* getRegisterList(unsigned int *num_registers);

        // Get register value
        VALUES readRegister(DEVICE device, REGISTER reg, uint32_t n);

        // Set register value
        ERROR writeRegister(DEVICE device, REGISTER reg, uint32_t n, uint32_t *value);

        // Asynchronously load firmware to FPGA.
        ERROR loadFirmware(DEVICE device, const char* bitstream);

        // Synchronously load firmware to FPGA
        ERROR loadFirmwareBlocking(DEVICE device, const char* bitstream);

    protected:
        // Initialise board
     //  ERROR initialiseBoard() { return SUCCESS; }
};

#endif // BOARD