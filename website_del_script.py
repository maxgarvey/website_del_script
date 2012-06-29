'''/website_del_script/website_del_script.py'''
from tempfile import TemporaryFile
from sys import exc_info
import argparse
import psuldap
import socket
import subprocess
import os

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
    #this part does all of the work. the rest just formats it.
    website, dns, vhost, uid, google_acct = get_website_py(website_input)
    #split up the dns entry, formatting for output
    output_string = 'website: ' + website + '\n' + 'dns: \n'
    for line in dns:
        if not (line.isspace() or line == ''):
            output_string += line + '\n'
    #add vhost stuff to output
    output_string += 'vhosts: \n'
    for line in vhost:
        if not (line.isspace() or line == ''):
            output_string += line + '\n'
    #catch the case where there's no vhosts
    if len(vhost) == 0:
        output_string += '\tno vhosts.\n'
    output_string += 'uid: \n\t' + uid + '\n\n'
    output_string += google_acct
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
        except IOError, err:
            print '\nerror occurred during grepping {0} directory: {1}'.format(
                my_type,err)

        temp_file.seek(0)
        file_string = temp_file.read()

    file_lines = file_string.split('\n')
    return file_lines

def process_lines(file_lines, whitelist_lines, start_dir):
    '''this method is a helper for figuring out which lines in our results are
    worthwhile and formatting them a little bit.'''
    keeper_lines = [] #the lines we will be keeping
    current_file = '' #the file being grepped (since there are usually multiple
                      #relevant lines per file).
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
    vhost_lines = process_lines(file_lines, whitelist_lines, __puppet_dir__)

    uid, _ = ldap_lookup(website)
    if uid == '':
        uid = 'no uid.'

    if uid != 'no uid.':
        #got to trim the bracket, and quote off both sides
        uid = uid[2:-2]
        google_acct = gam_lookup(uid)
    else:
        google_acct = 'no ldap uid found to check for google account.'

    return website, dns_lines, vhost_lines, uid, google_acct

def gam_lookup(ldap_uid):
    '''this is a helper method for looking up a google account for the website
        and returning it if it exists.'''
    with TemporaryFile() as temp:
        with TemporaryFile() as temperr:
            subprocess.call(['python', 'gam.py', 'info', 'user', ldap_uid], stdout=temp, stderr=temperr)
            temp.seek(0)
            gam_output = temp.read()

    if gam_output != None and gam_output != '':
        google_out_string = 'google account: {0}'.format(
            gam_output.split('\n')[0].split(': ')[1])
    else:
        google_out_string = 'no google account found for: user={0}'.format(
            ldap_uid)
    return google_out_string

#this will perform the function on a python list of URLs
def get_website_list( website_list ):
    '''looks up each URL from a list of urls.'''
    out_file = open( 'outfile.txt', 'w' )
    websites_str = ''

    for website in website_list:
        if website != '':
            website_str = get_website( str(website) )
            websites_str += website_str

    out_file.close()
    return websites_str

#this will work from a file with a URL on each line
def get_websites_from_file( input_file ):
    '''this method takes a file location as a string and reads it in, splitting
        on newlines and putting each URL through the lookup.'''
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

def ldap_connect():
    '''a helper method for connecting to ldap'''
    try:
        ldap_obj = psuldap.psuldap()
        ldap_obj.connect(ldapurl='ldap://ldap.oit.pdx.edu/')
        ldap_connected = True
        return ldap_obj, ldap_connected
    except psuldap.ldap.LDAPError, err:
        print '\nerror connecting to ldap: {0}\n'.format(err)
        return None, False

def ldap_search(ldap_obj, search_filter, ldap_searched, ldap_results):
    '''a helper method to handle ldap searches in the context of this specific
        app.'''
    search_results = []
    try:
        search_results = ldap_obj.search( searchfilter=search_filter )
        ldap_searched = True
        if len( search_results ) > 0:
            ldap_results.append( search_results )
    except psuldap.ldap.FILTER_ERROR, err:
        print '\nerror searching ldap\n {0}\n'.format(err)
    return ldap_searched, ldap_results, search_results

def ldap_lookup( website ):
    '''helper method for handling the ldap lookup'''
    ldap_connected = False
    ldap_searched = False
    search_results = []
    ldap_results = []
    
    ldap_obj, ldap_connected = ldap_connect()

    if ldap_connected:

        this_search_filter = '(&(eduPersonAffiliation=WEB)(labeledUri=*' + \
            str( website ) + '*))'
        ldap_searched, ldap_results, search_results = ldap_search(
            ldap_obj, this_search_filter, ldap_searched, ldap_results)

        if len( search_results ) is 0:
            this_search_filter = '(&(eduPersonAffiliation=WEB)(cn=*' + \
                str( website ) + '*))'
            try:
                search_results = ldap_obj.search( 
                    searchfilter=this_search_filter )
                ldap_searched = True
                if len( search_results ) > 0:
                    ldap_results.append( search_results )
            except psuldap.ldap.FILTER_ERROR, err:
                print '\nerror searching ldap\n{0}\n'.format(err)

        if len( search_results ) is 0:
            this_search_filter = '(&(eduPersonAffiliation=WEB)(gecos=*' + \
                str( website ) + '*))'
            try:
                search_results = ldap_obj.search( 
                    searchfilter=this_search_filter )
                ldap_searched = True
                if len( search_results ) > 0:
                    ldap_results.append( search_results )
            except psuldap.ldap.FILTER_ERROR, err:
                print '\nerror searching ldap\n{0}\n'.format(err)

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
    __input_entered__ = False

    try:
        __parser__ = argparse.ArgumentParser(description = \
            ('this script takes a website as input and finds the ip ' + \
            'address, indicating DNS records; checks in puppet for any ' + \
            'puppet records containing the file; and an ldap lookup to see ' + \
            'if there\'s a uid for the website'))
        __parser__.add_argument('website', action='store', nargs = '*')
        __args__ = __parser__.parse_args()
        for site in __args__.website:
            #if there are any args, input_entered is set to true
            if not __input_entered__:
                __input_entered__ = True
            print '\n' + str(get_website(site))

    except Exception, err:
        print 'error: {0}'.format(err)
        print get_website('')

    if not __input_entered__:
        print get_website('')
