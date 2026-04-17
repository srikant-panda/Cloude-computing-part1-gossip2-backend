/**********************************
 * FILE NAME: MP1Node.cpp
 *
 * DESCRIPTION: Membership protocol run by this Node.
 * 				Definition of MP1Node class functions.
 **********************************/

#include "MP1Node.h"
#include <string>

/*
 * Note: You can change/add any functions in MP1Node.{h,cpp}
 */

/**
 * Overloaded Constructor of the MP1Node class
 * You can add new members to the class if you think it
 * is necessary for your logic to work
 */
MP1Node::MP1Node(Member *member, Params *params, EmulNet *emul, Log *log, Address *address) {
    srand (time(NULL));
	for( int i = 0; i < 6; i++ ) {
		NULLADDR[i] = 0;
	}
	this->memberNode = member;
	this->emulNet = emul;
	this->log = log;
	this->par = params;
	this->memberNode->addr = *address;
}

/**
 * Destructor of the MP1Node class
 */
MP1Node::~MP1Node() {}

/**
 * FUNCTION NAME: recvLoop
 *
 * DESCRIPTION: This function receives message from the network and pushes into the queue
 * 				This function is called by a node to receive messages currently waiting for it
 */
int MP1Node::recvLoop() {
    if ( memberNode->bFailed ) {
    	return false;
    }
    else {
    	return emulNet->ENrecv(&(memberNode->addr), enqueueWrapper, NULL, 1, &(memberNode->mp1q));
    }
}

/**
 * FUNCTION NAME: enqueueWrapper
 *
 * DESCRIPTION: Enqueue the message from Emulnet into the queue
 */
int MP1Node::enqueueWrapper(void *env, char *buff, int size) {
	Queue q;
	return q.enqueue((queue<q_elt> *)env, (void *)buff, size);
}

/**
 * FUNCTION NAME: nodeStart
 *
 * DESCRIPTION: This function bootstraps the node
 * 				All initializations routines for a member.
 * 				Called by the application layer.
 */
void MP1Node::nodeStart(char *servaddrstr, short servport) {
    Address joinaddr;
    joinaddr = getJoinAddress();

    // Self booting routines
    if( initThisNode(&joinaddr) == -1 ) {
#ifdef DEBUGLOG
        log->LOG(&memberNode->addr, "init_thisnode failed. Exit.");
#endif
        exit(1);
    }

    if( !introduceSelfToGroup(&joinaddr) ) {
        finishUpThisNode();
#ifdef DEBUGLOG
        log->LOG(&memberNode->addr, "Unable to join self to group. Exiting.");
#endif
        exit(1);
    }

    return;
}

/**
 * FUNCTION NAME: initThisNode
 *
 * DESCRIPTION: Find out who I am and start up
 */
int MP1Node::initThisNode(Address *joinaddr) {
	/*
	 * This function is partially implemented and may require changes
	 */
    if(memberNode == nullptr) return -1;

	int id = *(int*)(&memberNode->addr.addr);
	int port = *(short*)(&memberNode->addr.addr[4]);

	memberNode->bFailed = false;
	memberNode->inited = true;
	memberNode->inGroup = false;
    // node is up!
	memberNode->nnb = 0;
	memberNode->heartbeat = 0;
	memberNode->pingCounter = TFAIL;
	memberNode->timeOutCounter = -1;
    initMemberListTable(memberNode);

    return 0;
}

/**
 * FUNCTION NAME: introduceSelfToGroup
 *
 * DESCRIPTION: Join the distributed system
 */
int MP1Node::introduceSelfToGroup(Address *joinaddr) {
	MessageHdr *msg;
#ifdef DEBUGLOG
    static char s[1024];
#endif

if(memberNode == nullptr) return 0;

    if ( 0 == memcmp((char *)&(memberNode->addr.addr), (char *)&(joinaddr->addr), sizeof(memberNode->addr.addr))) {
        // I am the group booter (first process to join the group). Boot up the group
#ifdef DEBUGLOG
        log->LOG(&memberNode->addr, "Starting up group...");
#endif
        memberNode->inGroup = true;
    }
    else {
        size_t msgsize = sizeof(MessageHdr) + sizeof(joinaddr->addr) + sizeof(long) + 1;
        msg = (MessageHdr *) malloc(msgsize * sizeof(char));

        // create JOINREQ message: format of data is {struct Address myaddr}
        msg->msgType = JOINREQ;
        memcpy((char *)(msg+1), &memberNode->addr.addr, sizeof(memberNode->addr.addr));
        memcpy((char *)(msg+1) + 1 + sizeof(memberNode->addr.addr), &memberNode->heartbeat, sizeof(long));

#ifdef DEBUGLOG
        sprintf(s, "Trying to join...");
        log->LOG(&memberNode->addr, s);
#endif

        // send JOINREQ message to introducer member
        emulNet->ENsend(&memberNode->addr, joinaddr, (char *)msg, msgsize);

        free(msg);
    }

    return 1;

}

/**
 * FUNCTION NAME: finishUpThisNode
 *
 * DESCRIPTION: Wind up this node and clean up state
 */
int MP1Node::finishUpThisNode(){
   /*
    * Your code goes here
    */
   return 0;
}

/**
 * FUNCTION NAME: nodeLoop
 *
 * DESCRIPTION: Executed periodically at each member
 * 				Check your messages in queue and perform membership protocol duties
 */
void MP1Node::nodeLoop() {
    if (memberNode->bFailed) {
    	return;
    }

    // Check my messages
    checkMessages();

    // Wait until you're in the group...
    if( !memberNode->inGroup ) {
    	return;
    }

    // ...then jump in and share your responsibilites!
    nodeLoopOps();

    return;
}

/**
 * FUNCTION NAME: checkMessages
 *
 * DESCRIPTION: Check messages in the queue and call the respective message handler
 */
void MP1Node::checkMessages() {
    void *ptr;
    int size;

    // Pop waiting messages from memberNode's mp1q
    while ( !memberNode->mp1q.empty() ) {
    	ptr = memberNode->mp1q.front().elt;
    	size = memberNode->mp1q.front().size;
    	memberNode->mp1q.pop();
    	recvCallBack((void *)memberNode, (char *)ptr, size);
    }
    return;
}

/**
 * FUNCTION NAME: recvCallBack
 *
 * DESCRIPTION: Message handler for different message types
 */
bool MP1Node::recvCallBack(void *env, char *data, int size ) {
    size_t msgsize = sizeof(MessageHdr) + sizeof(memberNode->addr) + 1 + sizeof(long);
    if(size < msgsize) return false;

    MessageHdr* msg = (MessageHdr*) data;
    Address* addr = (Address*) (msg+1);
    long* heartbeat = (long*) (data+sizeof(MessageHdr)+sizeof(Address)+1);
    
    switch (msg->msgType){
        case JOINREQ:{
            MessageHdr* reply = (MessageHdr *) malloc(msgsize * sizeof(char));
            reply->msgType = JOINREP;
            Address* toaddr = addr;
            memcpy((char *)(reply+1), &memberNode->addr, sizeof(memberNode->addr));
            memcpy((char *)(reply+1) + sizeof(memberNode->addr) + 1, &memberNode->heartbeat, sizeof(long));

            string logMsg = "Sending JOINREP to " + addr->getAddress() + " heartbeat " + to_string(memberNode->heartbeat);
            log->LOG(&memberNode->addr, logMsg.c_str());
            emulNet->ENsend(&memberNode->addr, toaddr, (char *)reply, msgsize);
	        free(reply);

            bool flag = updateMembershipList(addr, *heartbeat); // true: if either newly added node or latest heartbeat from exisintg node 
            if(flag) sendGossipHB(addr, *heartbeat);
            break;
        }
        case JOINREP:{
            memberNode->inGroup = true;
            long* heartbeat = (long*) (data+sizeof(MessageHdr)+ sizeof(Address) + 1);
            string logMsg = "JOINREP from " + addr->getAddress() + " data " + to_string(*heartbeat);
            log->LOG(&memberNode->addr, logMsg.c_str());
            break;
        }
        case HEARTBEAT:{
            bool flag = updateMembershipList(addr, *heartbeat); // true: if either newly added node or latest heartbeat from exisintg node 
            if(flag) sendGossipHB(addr, *heartbeat);
            break;
        }
        default:{
            break;
        }
    }
    return true;    
}



bool MP1Node::updateMembershipList(Address *addr, long heartbeat){
    for (auto& entry : memberNode->memberList) {
        Address* mle_addr = new Address(to_string(entry.getid())+":"+to_string(entry.getport()));
        if (*mle_addr == *addr) {
            if (heartbeat > entry.getheartbeat()) {
                entry.setheartbeat(heartbeat);
                entry.settimestamp(par->getcurrtime());
                return true;
            } else {
                return false;
            }
        }
    }
    // new addition to membership list
    MemberListEntry mle(*((int*)addr->addr),
						*((short*)&(addr->addr[4])),
						heartbeat,
						par->getcurrtime());
	memberNode->memberList.push_back(mle);
    log->logNodeAdd(&memberNode->addr, addr);
    return true;
}

void MP1Node::sendGossipHB(Address *addr, long heartbeat) {
    int fanout = memberNode->memberList.size() < FANOUT ? FANOUT : memberNode->memberList.size();
    
    MessageHdr *msg;
    size_t msgsize = sizeof(MessageHdr) + sizeof(addr->addr) + sizeof(long) + 1;
    msg = (MessageHdr *) malloc(msgsize * sizeof(char));
    msg->msgType = HEARTBEAT;
    memcpy((char *)(msg+1), addr->addr, sizeof(addr->addr));
    memcpy((char *)(msg+1) + sizeof(addr->addr) + 1, &heartbeat, sizeof(long));

    for (int i=0, tries = 0; tries < memberNode->memberList.size() and i < fanout; tries++) {
        int randomIdx = rand() % memberNode->memberList.size();
        MemberListEntry &mle = memberNode->memberList[randomIdx];
        Address mle_addr = Address(to_string(mle.getid())+":"+to_string(mle.getport()));
        
        if (mle_addr == memberNode->addr) continue;
        
        // send heartbeat to mle
        emulNet->ENsend(&memberNode->addr, &mle_addr, (char *)msg, msgsize);
        
        fanout++;
    }
    free(msg);
}

/**
 * FUNCTION NAME: nodeLoopOps
 *
 * DESCRIPTION: Check if any node hasn't responded within a timeout period and then delete
 * 				the nodes
 * 				Propagate your membership list
 */
void MP1Node::nodeLoopOps() {
    
    for (vector<MemberListEntry>::iterator it = memberNode->memberList.begin(); it != memberNode->memberList.end(); it++) {
        // time since last heartbeat greater than TREMOVE
        if (par->getcurrtime() - it->timestamp > TREMOVE) {
            Address mle_addr = Address(to_string(it->getid())+":"+to_string(it->getport()));
            string logMsg = "Timing out " + mle_addr.getAddress();
            log->LOG(&memberNode->addr, logMsg.c_str());
            // TODO: implement TFAIL
            // removing node 
            memberNode->memberList.erase(it);
            it--;
            log->logNodeRemove(&memberNode->addr, &mle_addr);
        }
    }    


    memberNode->heartbeat++;
    bool flag = updateMembershipList(&memberNode->addr, memberNode->heartbeat);
    if (flag) sendGossipHB(&memberNode->addr, memberNode->heartbeat);
    return;
}

/**
 * FUNCTION NAME: isNullAddress
 *
 * DESCRIPTION: Function checks if the address is NULL
 */
int MP1Node::isNullAddress(Address *addr) {
	return (memcmp(addr->addr, NULLADDR, 6) == 0 ? 1 : 0);
}

/**
 * FUNCTION NAME: getJoinAddress
 *
 * DESCRIPTION: Returns the Address of the coordinator
 */
Address MP1Node::getJoinAddress() {
    Address joinaddr;

    memset(&joinaddr, 0, sizeof(Address));
    *(int *)(&joinaddr.addr) = 1;
    *(short *)(&joinaddr.addr[4]) = 0;

    return joinaddr;
}

/**
 * FUNCTION NAME: initMemberListTable
 *
 * DESCRIPTION: Initialize the membership list
 */
void MP1Node::initMemberListTable(Member *memberNode) {
	memberNode->memberList.clear();
}

/**
 * FUNCTION NAME: printAddress
 *
 * DESCRIPTION: Print the Address
 */
void MP1Node::printAddress(Address *addr)
{
    printf("%d.%d.%d.%d:%d \n",  addr->addr[0],addr->addr[1],addr->addr[2],
                                                       addr->addr[3], *(short*)&addr->addr[4]) ;    
}
