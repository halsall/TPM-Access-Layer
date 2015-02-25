// Implements all functionality associated with the UCP protocol
// Handles all communication-related functionality

#ifndef PROTOCOL_CLASS
#define PROTOCOL_CLASS

#include <sys/socket.h>
#include <arpa/inet.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

#include "Definitions.hpp"

// Create protocol abstract class
class Protocol
{
    public:
        // Declare constructor for all protocols
        Protocol()     
        {
            // Initialise socket descriptor
            this -> sockfd = -1;
        }
        
    // Define functions to be implemented by derived classes
    public:
        // Create socket
        virtual ERROR createSocket(char *IP, int port) = 0;

        // Close socket
        virtual ERROR closeSocket() = 0;

        // Read register/memory area capability
        // This will take care of issuing multiple requests if 
        // the amount of data to read is larger than one UDP packet
        virtual VALUE readRegister(uint32_t address) = 0;

        // Write register/memory area capability
        // This will take care of issuing multiple requests if the 
        // amount of data to write is larger than one UDP packet    
        virtual ERROR writeRegister(uint32_t address, uint32_t value) = 0;

        // Accessors
        char *getIP() { return this -> ip; }
        unsigned short getPort() { return this -> port; }

    // Define functions and properties common to any derived classes, if any
    protected:
        char            *ip;  // Board IP address
        unsigned short  port; // Port to communicate with board

        struct sockaddr_in board_addr;  // Board address structure
        int                sockfd;      // Socket
};

// Protocol subclass implementing the UCP protocol
class UCP: public Protocol
{
    public:
        // UCP Constructor
        UCP();

    // Implement virtual functions
    public:
        ERROR createSocket(char *IP, int port);
        ERROR closeSocket();
        VALUE readRegister(uint32_t address);
        ERROR writeRegister(uint32_t address, uint32_t value);

    private:
        // Send packet
        ERROR sendPacket(char *message, size_t length);

        // Receive packet
        ssize_t receivePacket(char *buffer, size_t max_length);

    private:
        // Sequence number
        uint32_t  sequence_number;

    private:
    
        // OPCODE definitions 
        enum { OPCODE_READ             = 0x01, 
               OPCODE_WRITE            = 0x02, 
               OPCODE_BITWISE_AND      = 0x03,
               OPCODE_BITWISE_OR       = 0x04,
               OPCODE_FLASH_WRITE      = 0x06,
               OPCODE_FLASH_READ       = 0x07,
               OPCODE_FLASH_ERASE      = 0x08,
               OPCODE_FIFO_READ        = 0x09,
               OPCODE_FIFO_WRITE       = 0x0A,
               OPCODE_BIT_WRITE        = 0x0B,
               OPCODE_RESET_BOARD      = 0x11,
               OPCODE_PERIODIC_UPDATE  = 0x12,
               OPCODE_ASYNC_UPDATE     = 0x13,
               OPCODE_CANCEL_UPDATE    = 0x14,
               OPCOED_WAIT_FOR_PPS     = 0xFFFFFFFF} 
               OPCODE;

        // Packet structure definitions
        // NOTE: __packed__ makes sure that the values are packet
        //       together in memory (no gaps)

        // Generic UCP command header
        struct ucp_command_header
        {
            uint32_t psn;
            uint32_t opcode;
            uint32_t nvalues;
            uint32_t address;
        } __attribute__ ((__packed__));

        // UCP command packet 
        struct ucp_command_packet
        {
            struct ucp_command_header header;
            uint32_t data;
        } __attribute__ ((__packed__));


        // Generic UCP reply header
        struct ucp_reply_header 
        {
            uint32_t psn;
            uint32_t addr;
        } __attribute__ ((__packed__));

        // UCP write reply (N = 1)
        struct ucp_write_reply
        {
            struct ucp_reply_header header;
        } __attribute__ ((__packed__));

        // UCP read reply (N = 1)
        struct ucp_read_reply
        {
            struct ucp_reply_header header;
            uint32_t data;
        } __attribute__ ((__packed__));
};

#endif  // PROTOCOL
