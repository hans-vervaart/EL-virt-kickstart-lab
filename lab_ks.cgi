#!/bin/bash
#
# vim:tabstop=3:expandtab:shiftwidth=3
#
# GPLv3 see LICENCE file
#
# $Date: 2026-03-07 01:42:40 +0100 (Sat, 07 Mar 2026) $
# $Revision: 796 $
#
# This cgi script provides modified kickstart files
#
 
# Definitions

KSF_DIR=/var/www/html/ks-files

# extra functions
HexToChar()
{
   eval echo `echo "$1" | tr '[[:lower:]]' '[[:upper:]]' | \
   sed -e 's/./\0 /g' -e 's/A/10/g' -e 's/B/11/g' -e 's/C/12/g' \
       -e 's/D/13/g' -e 's/E/14/g'  -e 's/F/15/g' \
       -e 's/^[^ ]*/$(((\0*16)/' -e 's/ $/))/' -e 's/ /+/'`| \
   awk '{printf("%c",$1)}'
}

UrlEscapes2Text()
{
   while [ "$1" != "" ]
   do
      eval printf "%s" $(echo $1 | \
           sed 's/%\([0-9a-fA-F][0-9a-fA-F]\)/$(HexToChar \1)/g')
      shift
      if [ "$1" = "" ]
      then
         printf '\n'
      else
         printf ' '
      fi
   done
}

# Shell simulation / plain text mode
if [ "$QUERY_STRING" = "" ]
then
   # Copy $1 to QUERY_STRING, for command line testing
   QUERY_STRING=`echo $* | sed 's/[ ]/%20/g'`
else
   # Set output to plain text
   echo "Content-type: text/plain"
   echo
fi

# Maybe silly, but everything back to arguments
set -- `echo $QUERY_STRING | sed 's/%20/ /g'`

if [ $# -lt 2 ]
then
   echo
   echo "Usage:"
   echo
   echo "  `basename $0` ksfilename hostname [dev=Xd] [iso] [auto_ks_post=val]"
   echo
   echo "    or"
   echo
   Url="http://`hostname`/cgi-bin/`basename $0`"
   Url="${Url}?ksfilename%20hostname[%20dev=Xd][%20iso]"
   echo "  $Url"
   echo
   echo
   echo "  optional dev=Xd: disk device (sd=/dev/sda vd=/dev/vda hd=/dev/hda)"
   echo "  optional iso (flag)"
   echo "  optional auto_ks_post=val"
   echo
   exit 0
fi

KS_FILE=$1
shift
KS_HOST=$1
shift

while [ "$1" != "" ]
do
   if echo $1 | grep -q '='
   then
      if echo $1 | grep -q '%'
      then
         # translate hex chars and place single quotes around the value
         eval $(UrlEscapes2Text $1 | \
                sed -e 's/^\([a-z][a-z_]*\)=["'\'']*/\1='\''/' \
                    -e 's/^\([a-z][a-z_]*='\''[^"'\'']*\)["'\'']*$/\1'\''/') \
                 &> /dev/null
      else
         # good old method for the existing values
         eval $1 &> /dev/null
      fi
   else
      eval $1=yes
   fi
   shift
done

if [ "$dev" != "" ] && echo "$dev" | grep -q '^[hsv]d$'
then
   SedDiskDev=('-e' "s/\(d[ri][is][vk][^=]*=\)[hsv]d\([a-z]\)/\1$dev\2/g")
else
   unset SedDiskDev
fi

unset SedSeLinux
if [ "$se" != "" ]
then
   case $se in
      d)
         SedSeLinux=('-e' '/^selinux[[:space:]]/d' '-e' \
                     's/%packages.*/selinux --disabled\n\n\0/')
      ;;
      e)
         SedSeLinux=('-e' '/^selinux[[:space:]]/d' '-e' \
                     's/%packages.*/selinux --enforcing\n\n\0/')
      ;;
      p)
         SedSeLinux=('-e' '/^selinux[[:space:]]/d' '-e' \
                     's/%packages.*/selinux --permissive\n\n\0/')
      ;;
   esac
fi

if [ ! -f $KSF_DIR/$KS_FILE ]
then
   echo "ERROR: kickstartfile $KSF_DIR/$KS_FILE not found"
   exit 0
fi

#
# Set the variables from the kickstart file and KS_URL
#
eval `cat $KSF_DIR/$KS_FILE 2> /dev/null | 
      egrep '^#[_A-Z][_A-Z]*=|^url .*--url[= ]' | \
      sed -e 's/^url .*--url[= ]/KS_URL=/' -e 's/^#//' \
          -e 's/^AUTO_KS_POST=["'\'']*/AUTO_KS_POST='\''/' \
          -e 's/^\(AUTO_KS_POST='\''[^"'\'']*\)["'\'']*$/\1'\''/'` &> /dev/null
KS_URL=$(echo $KS_URL | sed 's,/*$,,')

# Correct the AUTO_KS_POST if passed from the url
unset AutoKsPost
if [ "$auto_ks_post" != "" ] && [ "$auto_ks_post" != "$AUTO_KS_POST" ]
then
   AUTO_KS_POST="$auto_ks_post"
   AutoKsPost=('-e' '/^#AUTO_KS_POST=/d' \
               '-e' '1i#AUTO_KS_POST='"'$AUTO_KS_POST'")
fi

#
# Retrieve the ip-address of the initial kickstart
#
# For DVD or CD (iso) install, provide the URL (CD(ROM)_URL= or DVD(ROM)_URL=)
# In the additional kickstart variables
#
UrlIp=$(echo $KS_URL | grep '^http://[0-9.]*/' | \
        sed -e 's,^http://\([0-9.]*\)/.*,\1,g' -e 's,[.],[.],g')

# Copy the server's IP to replace the original url IP in the kickstart file
if [ "$UrlIp" != "" ] && [ "$SERVER_ADDR" != "" ]
then
   SvrIp=$SERVER_ADDR
else
   unset UrlIp SvrIp
fi

# Add comment
echo "# This kickstart file ($KS_FILE) is modified by `basename $0`:"
echo "#"
echo "# 1. The clearpart, part, volgroup and logvol settings are un-hashed"
echo "# 2. The --hostname is added to the network settings"
echo "# 3. The --initlabel option is added to clearpart"
if echo $AUTO_KS_POST | egrep -i '^no|^off|^disabled' &> /dev/null
then
   echo "# 4. The .post script(s) are skipped (AUTO_KS_POST=$AUTO_KS_POST)"
elif echo $AUTO_KS_POST | egrep -i '^host' &> /dev/null
then
   if [ -f $KSF_DIR/.post/.$KS_HOST ]
   then
      PostScripts="$PostScripts .post/.$KS_HOST"
      echo "# 4. Added the (host) post script .post/.$KS_HOST as %post"
   fi
elif [ -f $KSF_DIR/.post ]
then
   PostScripts=.post
   echo "# 4. Added the hidden .post as %post"
elif [ -d $KSF_DIR/.post ] 
then
   Count=4
   if echo $AUTO_KS_POST | egrep '^egrep:' &> /dev/null
   then
      EregExpr="$(echo $AUTO_KS_POST | sed 's,^egrep:,,')"
   else
      EregExpr='*'
   fi
   PostScripts="`ls $KSF_DIR/.post | egrep "$EregExpr" | sed s,^,.post/,`"
   if [ "$PostScripts" != "" ]
   then
      echo "# $Count. Added $EregExpr post scripts from the .post/ dir as %post"
      Count=`expr $Count + 1`
   fi

   if [ -f $KSF_DIR/.post/.$KS_HOST ]
   then
      PostScripts="$PostScripts .post/.$KS_HOST"
      echo "# $Count. Added the (host) post script .post/.$KS_HOST dir as %post"
   fi
fi

echo "#"

if [ "$iso" = "yes" ] && [ "$KS_URL" != "" ] && [ "$ISO_MNT" != "" ]
then
   SedIso=('-e' 's/^url[[:space:]]--url.*/cdrom/' '-e' "s,$KS_URL,$ISO_MNT,g")
   # Add ks var with corrected ip for post-install to pick up
   echo "#ISO_URL=$KS_URL" | sed "s,http://$UrlIp/,http://$SvrIp/,g"
else
   unset SedIso
fi


# Modify the kickstart file
# 
# o Remove old hostname from the network command
# o Add the new host name to the network command
# o Remove all hashed out items for unattended install
#
sed -e 's/^network\(.*\) --hostname[ =][^ =]*\(.*\)/network\1\2/' \
    -e "s/^network\(.*\)/network\1 --hostname $KS_HOST/" \
    "${SedIso[@]}" \
    -e "s,http://$UrlIp/,http://$SvrIp/,g" \
    "${SedDiskDev[@]}" \
    "${SedSeLinux[@]}" \
    -e 's/^#\(clearpart \)/\1--initlabel /' \
    -e 's/^#\(part \)/\1/' \
    -e 's/^#\(volgroup \)/\1/' \
    -e 's/^#\(logvol \)/\1/' \
    -e 's/^#\(reboot\)/\1/' \
    -e 's/^#\(halt\)/\1/' \
    -e 's/^#\(poweroff\)/\1/' \
    "${AutoKsPost[@]}" \
    $KSF_DIR/$KS_FILE

# Add %post
for PostScript in $PostScripts
do
   # Setup the command array for adding logging
   unset DoPostLog
   if [ "$no_post_log" = "yes" ]
   then
      DoPostLog=(cat)
   else
      DoPostLog=(
      sed -e "\"s,^%post.*,\0\nLAB_KS_LOG=\\\$(ls -d \\\$ANA_INSTALL_PATH/root /root 2> /dev/null | head -1)/.lab_ks.post.log\n(\necho '##' start $PostScript\n(\n,\""
          -e "\"s,^%end.*,)\necho '##' end $PostScript rc=\\\$?\n)>>\\\$LAB_KS_LOG 2>\&1\n\0,\""
      )
   fi
   echo
   echo "##"
   echo "# post install script from $PostScript"
   echo
   (
      if ! head -5 $KSF_DIR/$PostScript | grep -q '^%post'
      then
         echo "%post"
      fi
      if grep '^LAB_KS_VARS=[ "]*[Yy]' $KSF_DIR/$PostScript &> /dev/null
      then
         echo "ISO_URL=$KS_URL" | sed "s,http://$UrlIp/,http://$SvrIp/,g"
         cat $KSF_DIR/$KS_FILE 2> /dev/null | grep '^#[_A-Z][_A-Z]*=' | \
         sed -e 's/^#//' -e "s,http://$UrlIp/,http://$SvrIp/,g"
      fi
      cat $KSF_DIR/$PostScript
      if ! tail -5 $KSF_DIR/$PostScript | grep -q '^%end'
      then
         echo "%end"
      fi
   ) | eval ${DoPostLog[@]}
done

