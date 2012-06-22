from tempfile import TemporaryFile
from sys import exc_info
import argparse
import getpass
import psuldap
import socket
import subprocess

#this global should be the location of the local copy of the puppet dir
puppet_dir = '/home/maxgarvey/mint_schizznatch'
dns_dir = '/home/maxgarvey/named.db' #and this one is a local copy of named.db

#the two whitelists
puppet_whitelist_addr = '/home/maxgarvey/mint_schizznatch/whitelist.txt'
dns_whitelist_addr = '/home/maxgarvey/named.db/whitelist.txt'

def get_website( website_input = '' ):
  '''this method puts the output of getting the website's information into a 
  string format... that way, when you want python structures, you can use get_website_py
  but otherwise, you can just get it as a string'''
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

#this method gets the website's info from various locations
def get_website_py( website_input = '' ):
  '''this method does all of the work of finding a single website's data; it 
  outputs a python list'''
  if website_input == '':
    #user input of the website url
    website = raw_input( "enter the website in question:\n\n" )
  else:
    website = website_input

  #standardizing so that it has or doesn't have versions with http or not
  if website.startswith( 'https://' ):
    website_no_http = website[8:]
  elif website.startswith( 'http://' ):
    website_no_http = website[7:]
  else:
    website_no_http = website

  '''this may be used later to check for www. at start of website. maybe check
  later for both cases'''
  if website_no_http.startswith( 'www.' ):
    website_no_www = website_no_http[4:]
  else:
    website_no_www = website_no_http

  #---------------------------------------
  #this part is all about the dns lookup

  dns_string = ''
  try:
    dns_string = socket.gethostbyname( website )
  except:
    dns_string = 'no dns.'

  keeper_lines = []
  keeper_lines.append( '\t' + dns_string )

  try:
    whitelist_file = open( dns_whitelist_addr, 'r' )
    whitelist_contents = whitelist_file.read( )
    whitelist_file.close( )
    whitelist_lines = whitelist_contents.split( '\n' )
  except:
    whitelist_lines = []
    print 'error working with whitelist file: ' + str( exc_info()[1] )

  with (TemporaryFile()) as temp_file:
    try:
      subprocess.call( ['grep', '-rn', website_no_www, dns_dir], stdout=temp_file, stderr=temp_file )
    except:
      print '\nerror occurred grepping dns dir: ' + str( exc_info()[1] )

    temp_file.seek(0)
    file_string = temp_file.read()

  file_lines = file_string.split('\n')

  current_file = ''
  for line in file_lines:
    if line.endswith('No such file or directory') or ( len(line) == 0 ):
      pass
    else:
      if line.startswith( dns_dir ):
        line = line[( len( dns_dir ) ):]
      whitelisted = False
      for prefix in whitelist_lines:
        if not (prefix.isspace() or prefix == ''):
          if line.startswith( prefix ):
            whitelisted = True
      if whitelisted == True:
        pass
      else:
        if current_file != line[:(line.index(':'))]:
          current_file = line[:(line.index(':'))]
          keeper_lines.append( ('\t' + current_file + ':') )
      keeper_lines.append( '\t\tline ' + str( line[(line.index(':')+1):line.index(':')+1+line[(line.index(':')+1):].index(':') ])
   + ': ' + str( line[(line.rindex(':')+1):] ) )

  dns = keeper_lines

  #---------------------------------------
  #this part is all about grepping the puppet directory structure, vhosts
  keeper_lines = []

  try:
    whitelist_file = open( puppet_whitelist_addr, 'r' )
    whitelist_contents = whitelist_file.read( )
    whitelist_file.close( )
    whitelist_lines = whitelist_contents.split( '\n' )
  except:
    whitelist_lines = []
    print 'error working with whitelist file: ' + str( exc_info()[1] )

  with (TemporaryFile()) as temp_file:
    try:
      subprocess.call( ['grep', '-rn', website_no_http, puppet_dir], stdout=temp_file, stderr=temp_file )
    except:
      print '\nerror occurred grepping puppet dir: ' + str( exc_info()[1] )

    temp_file.seek(0)
    file_string = temp_file.read()

  file_lines = file_string.split('\n')
  current_file = ''
  for line in file_lines:
    if line.endswith('No such file or directory') or ( len(line) == 0 ):
      pass
    else:
      if line.startswith( puppet_dir ):
        line = line[( len(puppet_dir) ):]
      whitelisted = False
      for prefix in whitelist_lines:
        if not (prefix.isspace() or prefix == ''):
          if line.startswith( prefix ):
            whitelisted = True
      if whitelisted == True:
        pass
      else:
        if current_file != line[:(line.index(':'))]:
          current_file = line[:(line.index(':'))]
          keeper_lines.append( ('\t' + current_file + ':') )
        keeper_lines.append( '\t\tline ' + str( line[(line.index(':')+1):line.index(':')+1+line[(line.index(':')+1):].index(':') ])
   + ': ' + str( line[(line.rindex(':')+1):] ) )

  vhost = keeper_lines

  uid, results = ldap_lookup( website_no_http )
  if uid == '':
    uid = 'no uid.'

  return website, dns, vhost, uid

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

def ldap_lookup( website_no_http ):
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
    this_search_filter = '(&(eduPersonAffiliation=WEB)(labeledUri=*' + str( website_no_http ) + '*))'
    try:
      search_results = ldap_obj.search( searchfilter=this_search_filter )
      ldap_searched = True
      if len( search_results ) > 0:
        ldap_results.append( search_results )
    except:
      print '\nerror searching ldap\n' + str( exc_info()[1] ) + '\n'

    if len( search_results ) is 0:
      this_search_filter = '(&(eduPersonAffiliation=WEB)(cn=*' + str( website_no_http ) + '*))'
      try:
        search_results = ldap_obj.search( searchfilter=this_search_filter )
        ldap_searched = True
        if len( search_results ) > 0:
         ldap_results.append( search_results )
      except:
        print '\nerror searching ldap\n' + str( exc_info()[1] ) + '\n'

    if len( search_results ) is 0:
      this_search_filter = '(&(eduPersonAffiliation=WEB)(gecos=*' + str( website_no_http ) + '*))'
      try:
        search_results = ldap_obj.search( searchfilter=this_search_filter )
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
    parser = argparse.ArgumentParser( description = 'this script takes a website as input and finds the ip address, indicating DNS records; checks in puppet for any puppet records containing the file; and an ldap lookup to see if there\'s a uid for the website' )
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
