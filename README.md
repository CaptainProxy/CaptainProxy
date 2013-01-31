CaptainProxy
============

A cheat for version 1.2.1 of the My Little Pony Android/iOS game.

This cheat is intended for advanced users only, and has very particular hardware requirements. You will need some sort of Linux-based router or firewall between your phone and the internet. Most consumer-grade routers will work for this, so if you have a Linksys, Buffalo, Actiontek, or similar router, you should be on the right track.

There are two steps to the cheat. Step one is to run the Python script on your computer. If you don't have Python installed yet, go to https://www.python.org/ to download it.

When the script starts up, it will ask you to enter your subnet and default gateway, so it can fill in the commands you'll need in part 2. If you're unfamiliar with these terms, make sure you educate yourself well first, because you will be messing with the internal operations of your router in part 2.

Make sure that any firewall on your computer is set to allow python.exe through. This script will serve as a proxy server for requests to the Gameloft servers. When it fields a request, it grabs the latest price list, caches it for an hour, modifies the data, and sends the response on.

Step two is to set up your router to intercept store requests and forward them to your computer. First, you will need to set up an SSH or Telnet password on your router. This will typically be done through the web administration interface. Then, log in over telnet or SSH, using PuTTY, HyperTerminal, or any other program. Run the three "iptables" commands you got from the Python script, and test it out. The iptables rules aren't saved, so whenever you reboot the router, you'll have to re-enter the rules. (Note: I have only tested this on one router, so you may need to change the interfaces br0 and eth0 to different interfaces depending on your hardware. Get in touch with me if you need help or figured it out on your own.)

Connect your phone to the Wi-Fi network and try running the game. If everything works, you'll see status messages in the output of the Python script, the game will finish booting, and the new prices will be applied to the shop. If the game hangs during startup, double check the firewall on your computer. If the game boots up but the prices don't change, double check the iptables rules.

Prices are rewritten according to the scheme /u/PrismaticMind from reddit used. Items that are purchased with gems or hearts are switched to bits, and the prices are multiplied by 100. Items that are acquired from the balloon game are switched to bits, and reverted to their latest price. (If you want everything to be free, change "* 100" to "* 0")

Thanks
======
Huge thanks to /u/PonyLiberator from reddit for his great work! Thanks to Suzuki Hisao, whose Tiny HTTP Proxy I based the Python script on. Thanks to the contributors to tldp.org, whose work I based the iptables rules on.

Future Work
===========
It would be nice to replace the iptables redirection with ARP spoofing, which would allow people with incompatible routers to use this cheat. I wasn't able to get ARP spoofing to work, but I did put together a filter for Ettercap along the way. (beware, untested) Take a look in the arpspoofing directory, and send me a pull request or email if you can help out.

Like so many software power struggles, cheating at MLP will always be an arms race. If Gameloft is still paying attention, they may patch the game again with more defensive mechanisms. Whatever their next move is, it will require more work than hardcoding an IP address. Presumably they will try some sort of encryption, either to obfuscate the XML file, sign the contents of the XML file, or to use TLS back to their server. In any case, I welcome the challenge. :D

