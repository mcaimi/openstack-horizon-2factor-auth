# Don't try fancy stuff like debuginfo, which is useless on binary-only
# packages. Don't strip binary too
# Be sure buildpolicy set to do nothing
%define        __spec_install_post %{nil}
%define          debug_package %{nil}
%define        __os_install_post %{_dbpath}/brp-compress
%define         temproot /tmp/temproot

Summary: Python HMAC/HOTP/TOTP Library
Name: python-otp-lib
Version: stein
Release: 1
License: GPL+
Group: Development/Tools
SOURCE0 : %{name}-%{version}.tar.gz
URL: https://github.com/mcaimi/python-otp-lib.git

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root

%description
%{summary}

%prep
%setup -q

%build
# Empty section.
python setup.py build

%install
rm -rf %{buildroot}
mkdir -p  %{buildroot}
mkdir -p %{temproot}
python setup.py install --root=%{temproot}

# in builddir
cp -a %{temproot}/* %{buildroot}

%clean
rm -rf %{buildroot}


%files
   /usr/lib/python2.7/site-packages/python_otp_lib-0.1-py2.7.egg-info/PKG-INFO
   /usr/lib/python2.7/site-packages/python_otp_lib-0.1-py2.7.egg-info/SOURCES.txt
   /usr/lib/python2.7/site-packages/python_otp_lib-0.1-py2.7.egg-info/dependency_links.txt
   /usr/lib/python2.7/site-packages/python_otp_lib-0.1-py2.7.egg-info/top_level.txt
   /usr/lib/python2.7/site-packages/rfc2104/__init__.py
   /usr/lib/python2.7/site-packages/rfc2104/__init__.pyc
   /usr/lib/python2.7/site-packages/rfc2104/hmac.py
   /usr/lib/python2.7/site-packages/rfc2104/hmac.pyc
   /usr/lib/python2.7/site-packages/rfc4226/__init__.py
   /usr/lib/python2.7/site-packages/rfc4226/__init__.pyc
   /usr/lib/python2.7/site-packages/rfc4226/hotp.py
   /usr/lib/python2.7/site-packages/rfc4226/hotp.pyc
   /usr/lib/python2.7/site-packages/rfc6238/__init__.py
   /usr/lib/python2.7/site-packages/rfc6238/__init__.pyc
   /usr/lib/python2.7/site-packages/rfc6238/totp.py
   /usr/lib/python2.7/site-packages/rfc6238/totp.pyc

%changelog

* Fri Oct 18 2019 Marco Caimi <marco.caimi> stein-1
        - Update version string after testing on Openstack Stein (RDO Stein)

* Tue Feb 12 2019 Marco Caimi <marco.caimi> queens-1
        - Update version string after testing on Openstack Queens (RDO Queens)

* Tue Aug 01 2017 Marco Caimi <marco.caimi> mitaka-1
        - Initial Porting Completed, target Openstack Mitaka (RHOSP 9.0)

