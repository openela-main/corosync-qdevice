# Conditionals
# Invoke "rpmbuild --without <feature>" or "rpmbuild --with <feature>"
# to disable or enable specific features
%bcond_without userflags
%bcond_with runautogen
%bcond_without systemd

%global gitver %{?numcomm:.%{numcomm}}%{?alphatag:.%{alphatag}}%{?dirty:.%{dirty}}
%global gittarver %{?numcomm:.%{numcomm}}%{?alphatag:-%{alphatag}}%{?dirty:-%{dirty}}

Name: corosync-qdevice
Summary: The Corosync Cluster Engine Qdevice
Version: 3.0.2
Release: 2%{?gitver}%{?dist}
License: BSD
URL: https://github.com/corosync/corosync-qdevice
Source0: https://github.com/corosync/corosync-qdevice/releases/download/v%{version}%{?gittarver}/%{name}-%{version}%{?gittarver}.tar.gz

Patch0: bz2181322-1-qdevice-Destroy-non-blocking-client-on-failure.patch

# Runtime bits
Requires: corosync >= 2.4.0
Requires: corosynclib >= 2.4.0
Requires: nss-tools

%if %{with systemd}
%{?systemd_requires}
BuildRequires: systemd
BuildRequires: systemd-devel
%else
Requires(post): /sbin/chkconfig
Requires(preun): /sbin/chkconfig
%endif

# Build bits
BuildRequires: gcc
BuildRequires: corosynclib-devel
BuildRequires: libqb-devel
BuildRequires: sed
BuildRequires: groff
BuildRequires: nss-devel

%if %{with runautogen}
BuildRequires: autoconf automake libtool
%endif

%prep
%setup -q -n %{name}-%{version}%{?gittarver}

%patch0 -p1 -b .bz2181322-1

%build
%if %{with runautogen}
./autogen.sh
%endif

%{configure} \
%if %{with userflags}
	--enable-user-flags \
%endif
%if %{with systemd}
	--enable-systemd \
%endif
	--enable-qdevices \
	--enable-qnetd \
	--with-initddir=%{_initrddir} \
	--with-systemddir=%{_unitdir} \
	--docdir=%{_docdir}

make %{_smp_mflags}

%install
make install DESTDIR=%{buildroot}

## tree fixup
# drop docs and html docs for now
rm -rf %{buildroot}%{_docdir}/*
mkdir -p %{buildroot}%{_sysconfdir}/sysconfig
# /etc/sysconfig/corosync-qdevice
install -p -m 644 init/corosync-qdevice.sysconfig.example \
   %{buildroot}%{_sysconfdir}/sysconfig/corosync-qdevice
# /etc/sysconfig/corosync-qnetd
install -p -m 644 init/corosync-qnetd.sysconfig.example \
   %{buildroot}%{_sysconfdir}/sysconfig/corosync-qnetd

%if %{with systemd}
sed -i -e 's/^#User=/User=/' \
   %{buildroot}%{_unitdir}/corosync-qnetd.service
%else
sed -i -e 's/^COROSYNC_QNETD_RUNAS=""$/COROSYNC_QNETD_RUNAS="coroqnetd"/' \
   %{buildroot}%{_sysconfdir}/sysconfig/corosync-qnetd
%endif

%description
This package contains the Corosync Cluster Engine Qdevice, script for creating
NSS certificates and an init script.

%post
%if %{with systemd} && 0%{?systemd_post:1}
%systemd_post corosync-qdevice.service
%else
if [ $1 -eq 1 ]; then
	/sbin/chkconfig --add corosync-qdevice || :
fi
%endif

%preun
%if %{with systemd} && 0%{?systemd_preun:1}
%systemd_preun corosync-qdevice.service
%else
if [ $1 -eq 0 ]; then
	/sbin/service corosync-qdevice stop &>/dev/null || :
	/sbin/chkconfig --del corosync-qdevice || :
fi
%endif

%postun
%if %{with systemd} && 0%{?systemd_postun:1}
%systemd_postun corosync-qdevice.service
%endif

%files
%license LICENSE
%dir %{_sysconfdir}/corosync/qdevice
%dir %config(noreplace) %{_sysconfdir}/corosync/qdevice/net
%dir %{_localstatedir}/run/corosync-qdevice
%{_sbindir}/corosync-qdevice
%{_sbindir}/corosync-qdevice-net-certutil
%{_sbindir}/corosync-qdevice-tool
%config(noreplace) %{_sysconfdir}/sysconfig/corosync-qdevice
%if %{with systemd}
%{_unitdir}/corosync-qdevice.service
%else
%{_initrddir}/corosync-qdevice
%endif
%{_mandir}/man8/corosync-qdevice-tool.8*
%{_mandir}/man8/corosync-qdevice-net-certutil.8*
%{_mandir}/man8/corosync-qdevice.8*

%package -n corosync-qdevice-devel
Summary: The Corosync Cluster Engine Qdevice Network Development Kit
Requires: pkgconfig

%description -n corosync-qdevice-devel
This package contains files used to develop using
The Corosync Cluster Engine Qdevice

%files -n corosync-qdevice-devel
%license LICENSE
%{_datadir}/pkgconfig/corosync-qdevice.pc

%package -n corosync-qnetd
Summary: The Corosync Cluster Engine Qdevice Network Daemon
Requires: nss-tools
Requires(pre): shadow-utils

%if %{with systemd}
%{?systemd_requires}
%endif

%description -n corosync-qnetd
This package contains the Corosync Cluster Engine Qdevice Network Daemon,
script for creating NSS certificates and an init script.

%pre -n corosync-qnetd
getent group coroqnetd >/dev/null || groupadd -r coroqnetd
getent passwd coroqnetd >/dev/null || \
    useradd -r -g coroqnetd -d / -s /sbin/nologin -c "User for corosync-qnetd" coroqnetd
exit 0

%post -n corosync-qnetd
%if %{with systemd} && 0%{?systemd_post:1}
%systemd_post corosync-qnetd.service
%else
if [ $1 -eq 1 ]; then
	/sbin/chkconfig --add corosync-qnetd || :
fi
%endif

%preun -n corosync-qnetd
%if %{with systemd} && 0%{?systemd_preun:1}
%systemd_preun corosync-qnetd.service
%else
if [ $1 -eq 0 ]; then
	/sbin/service corosync-qnetd stop &>/dev/null || :
	/sbin/chkconfig --del corosync-qnetd || :
fi
%endif

%postun -n corosync-qnetd
%if %{with systemd} && 0%{?systemd_postun:1}
%systemd_postun corosync-qnetd.service
%endif

%files -n corosync-qnetd
%license LICENSE
%dir %config(noreplace) %attr(770, coroqnetd, coroqnetd) %{_sysconfdir}/corosync/qnetd
%dir %attr(770, coroqnetd, coroqnetd) %{_localstatedir}/run/corosync-qnetd
%{_bindir}/corosync-qnetd
%{_bindir}/corosync-qnetd-certutil
%{_bindir}/corosync-qnetd-tool
%config(noreplace) %{_sysconfdir}/sysconfig/corosync-qnetd
%if %{with systemd}
%{_unitdir}/corosync-qnetd.service
%else
%{_initrddir}/corosync-qnetd
%endif
%{_mandir}/man8/corosync-qnetd-tool.8*
%{_mandir}/man8/corosync-qnetd-certutil.8*
%{_mandir}/man8/corosync-qnetd.8*

%changelog
* Thu Mar 23 2023 Jan Friesse <jfriesse@redhat.com> - 3.0.2-2
- Resolves: rhbz#2181322

- qdevice: Destroy non blocking client on failure (rhbz#2181322)
- merge upstream commit 4331c7d5650a8bf44c16512419f1954d0ef96df5 (rhbz#2181322)

* Thu Nov 03 2022 Jan Friesse <jfriesse@redhat.com> - 3.0.2-1
- Resolves: rhbz#2135862

- New upstream release

* Mon Nov 23 2020 Jan Friesse <jfriesse@redhat.com> - 3.0.1-1
- Resolves: rhbz#1752386
- Resolves: rhbz#1879351

- New upstream release

* Fri Apr 24 2020 Jan Friesse <jfriesse@redhat.com> 3.0.0-4
- Resolves: rhbz#1827256

- Add explicit corosync-qdevice and corosync-qnetd dependency for revdeps CI test

* Mon May 13 2019 Jan Friesse <jfriesse@redhat.com> 3.0.0-3
- Related: rhbz#1682124

- Add gating tests

* Wed Dec 12 2018 Jan Friesse <jfriesse@redhat.com> - 3.0.0-2
- Resolves: rhbz#1600919

- Fix spec file 2.93.0-1 entry removal

* Wed Dec 12 2018 Jan Friesse <jfriesse@redhat.com> - 3.0.0-1
- Resolves: rhbz#1600919

- New upstream release

* Fri Nov 23 2018 Jan Friesse <jfriesse@redhat.com> - 2.93.0-1
- Related: rhbz#1600919

- New upstream release

* Tue Sep 18 2018 Jan Friesse <jfriesse@redhat.com> 2.92.0-2
- Related: rhbz#1615945

- Rebuild for new LibQB

* Thu Aug 09 2018 Jan Friesse <jfriesse@redhat.com> - 2.92.0-1
- New upstream release

* Mon Jul 30 2018 Florian Weimer <fweimer@redhat.com> - 2.91.0-2
- Rebuild with fixed binutils

* Fri Apr 27 2018 Jan Friesse <jfriesse@redhat.com> - 2.91.0-1
- New upstream release

* Fri Apr 06 2018 Jan Friesse <jfriesse@redhat.com> - 2.90.0-5
- Import from Fedora

* Thu Mar 22 2018 Jan Friesse <jfriesse@redhat.com> - 2.90.0-4
- Rebuild for new Corosync

* Wed Feb 07 2018 Fedora Release Engineering <releng@fedoraproject.org> - 2.90.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Wed Jan 24 2018 Jan Friesse <jfriesse@redhat.com> - 2.90.0-2
- Fix spec file according to advices given in review by
  Robert-André Mauchin <zebob.m@gmail.com>

* Tue Jan 23 2018 Jan Friesse <jfriesse@redhat.com> - 2.90.0-1
- First upstream packaged version of corosync for rawhide review.
