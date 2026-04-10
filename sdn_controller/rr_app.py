"""
Ryu SDN Controller Application - Round Robin Load Balancer
"""

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from collections import defaultdict


class RoundRobinApp(app_manager.RyuApp):
    """Round Robin Load Balancing Application for Ryu SDN Controller"""
    
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    
    def __init__(self, *args, **kwargs):
        super(RoundRobinApp, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.round_robin_index = defaultdict(int)
    
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        # Install default flow to send unmatched packets to controller
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                         ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)
    
    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority, match=match,
                               instructions=inst)
        datapath.send_msg(mod)
    
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, msg):
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        
        pkt = packet.Packet(msg.data)
        
        # Get routing decision using round-robin
        switch_id = datapath.id
        available_ports = [p for p in range(1, 10) if p != in_port]
        
        if available_ports:
            out_port = available_ports[
                self.round_robin_index[switch_id] % len(available_ports)]
            self.round_robin_index[switch_id] += 1
        else:
            out_port = ofproto.OFPP_FLOOD
        
        actions = [parser.OFPActionOutput(out_port)]
        
        # Send packet out
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                 in_port=in_port, actions=actions,
                                 data=msg.data)
        datapath.send_msg(out)
