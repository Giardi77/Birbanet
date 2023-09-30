# Birbanet
A net tool based from the explaination on BHP about how to create a netcat-like tool

### How to run: 
cd Birbanet
(on listening machine)
python3 Birbanet.py -t {ip address} -p {port} -l -c
(on sender machine)
python Birbanet.py -t {ip address} -p {port}

###  fixes to do :
- upload feature is untested
- command 'cat' without params breaks the code on sender side
