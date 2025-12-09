# Perplexity API Response

## Prompt
```
Can you make me a basic home network topology diagram and guide to set this up. Can you insert a mermaid network diagram?
```

## Response
Here is a **basic home network topology diagram** using a **star topology**, which is the most common and simple setup for home networks. It includes an ISP modem, a Wi-Fi router, a network switch (optional for more wired devices), and multiple wired and wireless devices.

```mermaid
graph TD
    ISP[ISP Modem] --> Router[Wi-Fi Router]
    Router --> Switch[Network Switch]
    Switch --> PC1[Desktop PC]
    Switch --> TV[Smart TV]
    Switch --> Printer[Network Printer]
    Router --> Laptop[Laptop (Wi-Fi)]
    Router --> Phone[Smartphone (Wi-Fi)]
    Router --> Tablet[Tablet (Wi-Fi)]
```

### Guide to Set Up This Basic Home Network

1. **ISP Modem**  
   Connect your ISP-provided modem to the internet service line (cable, DSL, fiber).

2. **Wi-Fi Router**  
   Connect the modem to the WAN/Internet port of your Wi-Fi router using an Ethernet cable. This router will manage your home network and provide wireless access.

3. **Network Switch (Optional)**  
   If you have more than 4 wired devices, connect a network switch to one of the LAN ports on your router. This expands the number of wired connections available.

4. **Wired Devices**  
   Connect wired devices such as desktop PCs, smart TVs, and printers to the switch or directly to the router LAN ports via Ethernet cables.

5. **Wireless Devices**  
   Connect laptops, smartphones, tablets, and other Wi-Fi-enabled devices wirelessly to the router’s Wi-Fi network. Configure the Wi-Fi network with a secure password.

6. **Configure Router Settings**  
   - Change the default admin password of the router.  
   - Set up Wi-Fi SSID (network name) and password.  
   - Enable WPA3 or WPA2 encryption for security.  
   - Optionally, configure guest Wi-Fi for visitors.

7. **Test Connectivity**  
   Ensure all devices can access the internet and communicate within the home network (e.g., printing from PCs to the printer).

This setup provides a secure and scalable home network with both wired and wireless connectivity, suitable for typical home use including streaming, gaming, and office work[1][3][5].

## Citations
- https://www.edrawsoft.com/article/home-network-diagram.html
- https://www.auvik.com/franklyit/blog/effective-network-diagrams/
- https://lazyadmin.nl/home-network/home-network-diagram/
- https://creately.com/guides/cisco-templates/
- https://www.itjones.com/blogs/2020/11/22/a-guide-to-network-topology
- https://nulab.com/learn/software-development/network-diagrams-guide/
- https://www.youtube.com/watch?v=FjbyGydCdMc
- https://www.gliffy.com/blog/network-diagram-examples
