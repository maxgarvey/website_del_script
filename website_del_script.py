'''/website_del_script/website_del_script.py'''
from tempfile import TemporaryFile
from sys import exc_info
import argparse
import psuldap
import socket
import subprocess

#this global should be the location of the local copy of the puppet dir
__puppet_dir__ = '/home/maxgarvey/mint_stuff'
#and this one is a local copy of named.db
__dns_dir__ = '/home/maxgarvey/bind_stuff/named.db'

#the two whitelists
__puppet_whitelist_addr__ = '/home/maxgarvey/mint_stuff/whitelist.txt'
__dns_whitelist_addr__ = '/home/maxgarvey/bind_stuff/whitelist.txt'

def get_website( website_input = '' ):
    '''this method puts the output of getting the website's information into a 
    string format... that way, when you want python structures, you can use 
    get_website_py but otherwise, you can just get it as a string'''
    website, dns, vhost, uid = get_website_py( website_input )
    output_string = 'website: ' + website + '\n' + 'dns: \n' 
    for line in dns:
        if not ( line.isspace() or line == '' ):
            output_string += line + '\n'
    output_string += 'vhosts: \n'
    for line in vhost:
        if not ( line.isspace() or line == '' ):
            output_string += line + '\n'
    if len(vhost) == 0:
        output_string += '\tno vhosts.\n'
    output_string += 'uid: \n\t' + uid + '\n\n'
    return output_string

def strip_http(website_http):
    '''this method is a helper method to strip off the http or https from the
    front of a website.'''
    if website_http.startswith('https://'):
        website_no_http = website_http[8:]
    elif website_http.startswith('http://'):
        website_no_http = website_http[7:]
    else:
        website_no_http = website_http
    return website_no_http

def strip_www(website_www):
    '''this method is a helper method to strip off the www from the front of
    a website.'''
    if website_www.startswith( 'www.' ):
        website_no_www = website_www[4:]
    else:
        website_no_www = website_www
    return website_no_www

def dns_lookup(website):
    '''this method looks up a website to get the IP address that corresponds
    to it.'''
    dns_string = ''
    try:
        dns_string = socket.gethostbyname( website )
    except socket.error:
        dns_string = 'no dns.'
    return dns_string

def read_whitelist(location):
    '''this method reads in the whitelist given the path to the whitelist'''
    try:
        whitelist_file = open(location, 'r' )
        whitelist_contents = whitelist_file.read( )
        whitelist_file.close( )
        whitelist_lines = whitelist_contents.split( '\n' )
    except IOError:
        whitelist_lines = []
        print 'error working with whitelist file: ' + str( exc_info()[1] )
    return whitelist_lines

def find_lines(website, dns_dir, my_type='dns'):
    '''this method actually greps the directory for items with the website
    we're looking for.'''
    with (TemporaryFile()) as temp_file:
        try:
            subprocess.call( ['grep', '-rn', website, dns_dir], 
                stdout=temp_file, stderr=temp_file )
        except:
            print '\nerror occurred during grepping '+my_type+' directory: ' + \
                str( exc_info()[1] )

        temp_file.seek(0)
        file_string = temp_file.read()

    file_lines = file_string.split('\n')
    return file_lines

def process_lines(file_lines, whitelist_lines, start_dir):
    keeper_lines = []
    current_file = ''
    for line in file_lines:
        #if the line isn't relevant, ignore it.
        if line.endswith('No such file or directory') or ( len(line) == 0 ):
            pass
        else:
            #otherwise, skip past the part of the path that we know.
            if line.startswith(start_dir):
                line = line[(len(start_dir)):]
            whitelisted = False
            #compare with each element from whitelist, if the path starts with
            #a whitelisted prefix, then ignore it.
            for prefix in whitelist_lines:
                if not (prefix.isspace() or prefix == ''):
                    if line.startswith(prefix):
                        whitelisted = True
            if whitelisted == True:
                pass
            #if not whitelisted, add the filename and the relevant file contents
            #properly tabbed for easy reading.
            else:
                if current_file != line[:(line.index(':'))]:
                    current_file = line[:(line.index(':'))]
                    keeper_lines.append( ('\t' + current_file + ':') )
                keeper_lines.append( '\t\tline ' + str(
                    line[(line.index(':')+1):line.index(':')+1+\
                    line[(line.index(':')+1):].index(':') ])
                    + ': ' + str( line[(line.rindex(':')+1):] ) )
    return keeper_lines

def process_lines_debug(file_lines, whitelist_lines, start_dir):
    keeper_lines = []
    current_file = ''
    for line in file_lines:
        #if the line isn't relevant, ignore it.
        if line.endswith('No such file or directory') or ( len(line) == 0 ):
            pass
        else:
            #otherwise, skip past the part of the path that we know.
            if line.startswith(start_dir):
                line = line[(len(start_dir)):]
            whitelisted = False
            #compare with each element from whitelist, if the path starts with
            #a whitelisted prefix, then ignore it.
            for prefix in whitelist_lines:
                if not (prefix.isspace() or prefix == ''):
                    if line.startswith(prefix):
                        whitelisted = True
            if whitelisted == True:
                pass
            #if not whitelisted, add the filename and the relevant file contents
            #properly tabbed for easy reading.
            else:
                if current_file != line[:(line.index(':'))]:
                    current_file = line[:(line.index(':'))]
                    keeper_lines.append( ('\t' + current_file + ':') )
                keeper_lines.append( '\t\tline ' + str(
                    line[(line.index(':')+1):line.index(':')+1+\
                    line[(line.index(':')+1):].index(':') ])
                    + ': ' + str( line[(line.rindex(':')+1):] ) )
    return keeper_lines

#this method gets the website's info from various locations
def get_website_py( website_input = '' ):
    '''this method does all of the work of finding a single website's data; it 
    outputs a python list'''
    if website_input == '':
        #user input of the website url
        website = raw_input("enter the website to delete:\n")
        while website == '':
            website = raw_input("enter the website to delete:\n")
    else:
        website = website_input

    website = strip_http(website)
    website = strip_www(website)

    #this line finds the ip address of the website
    dns = dns_lookup(website)

    #this part greps the dns/bind stuff
    whitelist_lines = read_whitelist(__dns_whitelist_addr__)
    file_lines = find_lines(website, __dns_dir__)
    dns_lines = process_lines(file_lines, whitelist_lines, __dns_dir__)

    #prepend ip address to the dns information
    dns_lines.insert(0,('\t' + dns))

    #this part greps the puppet directory structure for vhosts
    whitelist_lines = read_whitelist(__puppet_whitelist_addr__)
    file_lines = find_lines(website, __puppet_dir__)
    vhost_lines = process_lines_debug(file_lines,
        whitelist_lines, __puppet_dir__)

    uid, results = ldap_lookup( website )
    if uid == '':
        uid = 'no uid.'

    return website, dns_lines, vhost_lines, uid

#this will perform the function on a python list of URLs
def get_website_list( website_list ):
    out_file = open( 'outfile.txt', 'w' )
    websites_str = '' 

    for website in website_list:
        if website != '':
            website_str = get_website( str(website) )
            websites_str += website_str

    out_file.close()
    out_file = open( 'outfile.txt', 'r' )
    filestring = out_file.read()
    return websites_str

#this will work from a file with a URL on each line
def get_websites_from_file( input_file ):
    with open( input_file, 'r' ) as in_file:
        filestring = in_file.read()
        my_list = filestring.split('\n')
        output_list = get_website_list( my_list )
        return output_list

def file_to_file( input_file, output_file ):
    '''performs operations on each line of the input file, and writes the output
    to the output file.'''
    output = get_websites_from_file( input_file )
    with open( output_file, 'w' ) as output_file:
        output_file.write( output )

def ldap_lookup( website ):
    '''helper method for handling the ldap lookup'''
    ldap_connected = False
    ldap_searched = False
    search_results = []
    ldap_results = []

    try:
        ldap_obj = psuldap.psuldap()
        ldap_obj.connect(ldapurl='ldap://ldap.oit.pdx.edu/')
        ldap_connected = True
    except:
        print '\nerror connecting to ldap\n'

    if ldap_connected:
        this_search_filter = '(&(eduPersonAffiliation=WEB)(labeledUri=*' + \
            str( website ) + '*))'
        try:
            search_results = ldap_obj.search( searchfilter=this_search_filter )
            ldap_searched = True
            if len( search_results ) > 0:
                ldap_results.append( search_results )
        except:
            print '\nerror searching ldap\n' + str( exc_info()[1] ) + '\n'

        if len( search_results ) is 0:
            this_search_filter = '(&(eduPersonAffiliation=WEB)(cn=*' + \
                str( website ) + '*))'
            try:
                search_results = ldap_obj.search( 
                    searchfilter=this_search_filter )
                ldap_searched = True
                if len( search_results ) > 0:
                    ldap_results.append( search_results )
            except:
                print '\nerror searching ldap\n' + str( exc_info()[1] ) + '\n'

        if len( search_results ) is 0:
            this_search_filter = '(&(eduPersonAffiliation=WEB)(gecos=*' + \
                str( website ) + '*))'
            try:
                search_results = ldap_obj.search( 
                    searchfilter=this_search_filter )
                ldap_searched = True
                if len( search_results ) > 0:
                    ldap_results.append( search_results )
            except:
                print '\nerror searching ldap\n' + str( exc_info()[1] ) + '\n'

    #ldap searched will always be true provided there was no error
    if ldap_searched:
        if len( search_results ) is 0:
            uid = ''
        else:
            uid = str( search_results[0][1]['uid'])
    else:
        uid = ''

    return uid, search_results

if __name__ == '__main__':
    '''the main method for when the function is called from the command line'''
    input_entered = False

    try:
        parser = argparse.ArgumentParser( description = \
            ('this script takes a website as input and finds the ip ' + \
            'address, indicating DNS records; checks in puppet for any ' + \
            'puppet records containing the file; and an ldap lookup to see ' + \
            'if there\'s a uid for the website') )
        parser.add_argument( 'website', action='store', nargs = '*' )
        args = parser.parse_args()
        for site in args.website:
            if not input_entered:
                input_entered = True
            print '\n' + str( get_website( site ) )

    except:
        print 'error: ' + str( exc_info()[1] )
        print get_website('')

    if not input_entered:
        print get_website('')
