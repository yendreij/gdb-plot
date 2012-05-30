#!/usr/bin/python

__author__="Brian Hone"

import sys, os, string, time, pprint
import numpy as np
import scipy.io as sio
import gdb

def get_data( args ):
    data = {}
    I = 1j
    for arg in args:
        # If we're dealing with sub-structures, descend down
        if arg.find('.') >=0 :
            arg_split = arg.split( '.' )
            x = gdb.selected_frame().read_var(arg_split[0])
            for i in arg_split[1:]:
                x = x[i]
        # Else, just get the data
        else:
            print arg
            try: ## try a stack variable
                x = gdb.selected_frame().read_var(arg)
            except: ## try a class member
                x = gdb.selected_frame().read_var("this").dereference()[arg]
        x_str = str(x)
        ########################################
        # BOOST VECTOR
        ########################################
        if x_str.find( "boost" ) >= 0:
            ptr = x['data_']['data_']
            size = x['data_']['size_']
            vals = []
            ## NOT COMPLEX
            if x_str.find( 'std::complex' ) < 0:
                for i in range( size ):
                    loc = ptr + i
                    vals.append( eval( str(loc.dereference() )) )
                u = np.array( vals )
                data[ arg ] = u
            ## COMPLEX
            else:
                for i in range( size ):
                    loc = ptr + i
                    vals.append( eval( str(loc.dereference()['_M_value'])) )
                u = np.array( vals ) 
                data[ arg ] = u
        ########################################
        # STL VECTOR
        ########################################
        elif x_str.find( "std::vector" ) >= 0:
            ptr = x['_M_impl']['_M_start']
            end = x['_M_impl']['_M_finish']
            vals = []
            ## COMPLEX
            if str(x.type).find( 'std::complex' ) >= 0:
                while ptr != end:
                    vals.append( eval( str( ptr.dereference()['_M_value'] ) ) )
                    ptr = ptr + 1
                u = np.array(vals)
                data[ arg ] = u
            ## Not Complex
            else:
                while ptr != end:
                    vals.append( eval( str( ptr.dereference() ) ) )
                    ptr = ptr + 1
                u = np.array(vals)
                data[ arg ] = u
        ########################################
        # Eigen
        ########################################
        elif x_str.find( "Eigen::Array" ) >= 0:
            #
            # NOTE: This only works for dynamic Eigen::Array 
            #
            if x_str.find("std::complex") >= 0:
                ptr = x['m_storage']['m_data']
                end = x['m_storage']['m_rows']
                vals = []
                for i in range(end):
                    vals.append( eval( str( ptr.dereference()['_M_value'] ) ) ) 
                    ptr = ptr + 1
                u = np.array( vals ) 
                data[ arg ] = u
            else:
                ptr = x['m_storage']['m_data']
                end = x['m_storage']['m_rows']
                vals = []
                for i in range(end):
                    vals.append( ptr.dereference() ) 
                    ptr = ptr + 1
                u = np.array( vals ) 
                data[ arg ] = u

        ########################################
        # Unknown, try parsing the string
        ########################################
        else:
            brace_pos = x_str.find('{') 
            brace_pos2 = x_str.find('}')
            x_str = '[ %s ]' % x_str[ brace_pos+1:brace_pos2]
            s = eval( '%s' % x_str )
            u = np.array( s ) 
            data[ arg ] = u

    return data
# end get_data

class MatSaver( gdb.Command ):
    def __init__( self ):
        super( MatSaver, self ).__init__("savemat", gdb.COMMAND_OBSCURE )

    def invoke( self, arg, from_tty ):
        args = string.split( arg )
        fname = args[0]
        data = get_data( args[1:] )
        for key, val in data.items():
            print "Saving %s" % key   
        sio.savemat( fname, data )
# end class Plotter

MatSaver()