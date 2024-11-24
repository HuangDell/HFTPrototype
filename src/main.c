#include <rte_eal.h>
#include <rte_ethdev.h>
#include <rte_mbuf.h>
#include "protocol_handler.h"
#include "arp_handler.h"
#include "udp_handler.h"
#include "roce_handler.h"

#define RX_RING_SIZE 128
#define TX_RING_SIZE 128
#define NUM_MBUFS 8191
#define MBUF_CACHE_SIZE 250
#define BURST_SIZE 32

static const char LOCAL_IP[]="10.10.10.3";

static const struct rte_eth_conf port_conf_default = {
    .rxmode = {
        .max_lro_pkt_size = RTE_ETHER_MAX_LEN,
    },
};

static struct rte_mempool *mbuf_pool = NULL;

static int port_init(uint16_t port) {
    struct rte_eth_conf port_conf = port_conf_default;
    const uint16_t rx_rings = 1, tx_rings = 1;
    uint16_t nb_rxd = RX_RING_SIZE;
    uint16_t nb_txd = TX_RING_SIZE;
    int retval;
    uint16_t q;
    struct rte_eth_dev_info dev_info;
    struct rte_eth_txconf txconf;    
    struct rte_eth_rxconf rxconf;

    if (!rte_eth_dev_is_valid_port(port))
        return -1;

    retval = rte_eth_dev_info_get(port, &dev_info);
    if (retval != 0) {
        printf("Error during getting device (port %u) info: %s\n",
                port, strerror(-retval));
        return retval;
    }
    // dev_info.default_rxconf.offloads |= RTE_ETH_RX_OFFLOAD_UDP_CKSUM;  
    // dev_info.default_txconf.offloads |= RTE_ETH_TX_OFFLOAD_UDP_CKSUM;  

    // if (dev_info.tx_offload_capa & RTE_ETH_TX_OFFLOAD_MBUF_FAST_FREE)
    //     port_conf.txmode.offloads |= RTE_ETH_TX_OFFLOAD_MBUF_FAST_FREE;

    /* Configure the Ethernet device */
    retval = rte_eth_dev_configure(port, rx_rings, tx_rings, &port_conf);
    if (retval != 0)
        return retval;

    retval = rte_eth_dev_adjust_nb_rx_tx_desc(port, &nb_rxd, &nb_txd);
    if (retval != 0)
        return retval;

    fflush(stdout);    
    rxconf = dev_info.default_rxconf;
    rxconf.offloads = port_conf.rxmode.offloads;

    /* Allocate and set up 1 RX queue per Ethernet port */
    for (q = 0; q < rx_rings; q++) {
        retval = rte_eth_rx_queue_setup(port, q, nb_rxd,
                rte_eth_dev_socket_id(port), &rxconf, mbuf_pool);
        if (retval < 0)
            return retval;
    }


    fflush(stdout);    
    txconf = dev_info.default_txconf;
    txconf.offloads = port_conf.txmode.offloads;
    /* Allocate and set up 1 TX queue per Ethernet port */
    for (q = 0; q < tx_rings; q++) {
        retval = rte_eth_tx_queue_setup(port, q, nb_txd,
                rte_eth_dev_socket_id(port), &txconf);
        if (retval < 0)
            return retval;
    }

    /* Start the Ethernet port */
    retval = rte_eth_dev_start(port);
    if (retval < 0)
        return retval;

    /* Enable RX in promiscuous mode for the Ethernet device */
    retval = rte_eth_promiscuous_enable(port);
    if (retval != 0)
        return retval;

    // 获取并打印链路状态  
    struct rte_eth_link link;  
    rte_eth_link_get_nowait(port, &link);  
    printf("Port %u configuration:\n", port);  
    if (link.link_status) {  
        printf("Port %d Link Up - speed %u Mbps - %s\n",  
               port, link.link_speed,  
               (link.link_duplex == RTE_ETH_LINK_FULL_DUPLEX) ?  
               "full-duplex" : "half-duplex");  
    } else {  
        printf("Port %d Link Down\n", port);  
    }  
    printf("  Promiscuous mode: %s\n", rte_eth_promiscuous_get(port) ? "enabled" : "disabled");  
    printf("  Allmulticast mode: %s\n", rte_eth_allmulticast_get(port) ? "enabled" : "disabled");  
    printf("  RX descriptors: %u\n", nb_rxd);  
    printf("  TX descriptors: %u\n", nb_txd);  
    printf("  RX offload flags: 0x%lx\n", port_conf.rxmode.offloads);  
    printf("  TX offload flags: 0x%lx\n", port_conf.txmode.offloads);  
    
    printf("  Driver name: %s\n", dev_info.driver_name);  
    printf("  Max rx queues: %u\n", dev_info.max_rx_queues);  
    printf("  Max tx queues: %u\n", dev_info.max_tx_queues);  
    return 0;
}

static void packet_processing_loop(void) {
    struct rte_mbuf *pkts_burst[BURST_SIZE];
    uint16_t port = 0;  // 使用第一个端口
    uint16_t nb_rx;
    uint32_t i;
    struct rte_ether_hdr *eth_hdr;
    char src_mac[RTE_ETHER_ADDR_FMT_SIZE];
    char dst_mac[RTE_ETHER_ADDR_FMT_SIZE];
    char src_ip[16];
    char dst_ip[16];

    printf("\nCore %u processing packets. [Ctrl+C to quit]\n", rte_lcore_id());

    int pkg_counter=0;
    while (1) {
        // 接收数据包
        nb_rx = rte_eth_rx_burst(port, 0, pkts_burst, BURST_SIZE);
        if (nb_rx == 0)
            continue;

        // 处理接收到的每个数据包
        for (i = 0; i < nb_rx; i++) {
            // eth_hdr = rte_pktmbuf_mtod(pkts_burst[i], struct rte_ether_hdr *);
            // /* Format MAC addresses */
            // rte_ether_format_addr(src_mac, RTE_ETHER_ADDR_FMT_SIZE, &eth_hdr->src_addr);
            // rte_ether_format_addr(dst_mac, RTE_ETHER_ADDR_FMT_SIZE, &eth_hdr->dst_addr);
            // printf("\nPacket %d:\n", pkg_counter++);
            // printf("  MAC: %s -> %s\n", src_mac, dst_mac);
            // printf("  Ether Type: 0x%04x\n", rte_be_to_cpu_16(eth_hdr->ether_type));

            process_packet(mbuf_pool,pkts_burst[i], port);
            rte_pktmbuf_free(pkts_burst[i]);
        }
    }
}

int main(int argc, char *argv[]) {
    uint16_t port = 0;
    int ret;

    /* Initialize the Environment Abstraction Layer (EAL) */
    ret = rte_eal_init(argc, argv);
    if (ret < 0)
        rte_exit(EXIT_FAILURE, "Error with EAL initialization\n");

    /* Check that there is an available port */
    if (rte_eth_dev_count_avail() == 0)
        rte_exit(EXIT_FAILURE, "Error: no available ports\n");

    /* Creates a new mempool in memory to hold the mbufs */
    mbuf_pool = rte_pktmbuf_pool_create("MBUF_POOL", NUM_MBUFS,
        MBUF_CACHE_SIZE, 0, RTE_MBUF_DEFAULT_BUF_SIZE + RTE_PKTMBUF_HEADROOM, rte_socket_id());

    if (mbuf_pool == NULL)
        rte_exit(EXIT_FAILURE, "Cannot create mbuf pool\n");

    /* Initialize port */
    if (port_init(port) != 0)
        rte_exit(EXIT_FAILURE, "Cannot init port %"PRIu16 "\n", port);

    /* Initialize protocol handlers */
    init_protocol_handlers();
    
    /* Initialize ARP handler */
    if (init_arp_handler(LOCAL_IP) != 0)  // 设置本机IP地址
        rte_exit(EXIT_FAILURE, "Cannot initialize ARP handler\n");

    /* Initialize UDP handler */
    if (init_udp_handler(LOCAL_IP) != 0)  // 设置本机IP地址
        rte_exit(EXIT_FAILURE, "Cannot initialize UDP handler\n");

    /* Register protocol handlers */
    register_protocol_handler(RTE_ETHER_TYPE_ARP, handle_arp_packet);
    // register_protocol_handler(RTE_ETHER_TYPE_IPV4, handle_udp_packet);
    register_protocol_handler(RTE_ETHER_TYPE_IPV4, handle_roce_packet);

    printf("Starting packet processing...\n");

    /* Call packet processing loop */
    packet_processing_loop();

    /* Clean up */
    rte_eal_cleanup();

    return 0;
}
