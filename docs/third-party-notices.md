# Third-party notices

The storefront self-hosts Inter and Cormorant Garamond; their notices sit alongside the font
files and their sources and checksums are in `static/fonts/font-manifest.json`. Jost was removed
on 2026-10-22 with the withdrawn campaign revision and is no longer distributed.
No Dior fonts, trademarks, photography or source bundles are distributed as project assets.

Gunicorn 26.2.0 is an MIT-licensed runtime dependency. Its installed package contains the upstream
license; see [Gunicorn's source/license](https://github.com/benoitc/gunicorn/blob/master/LICENSE).
The optional container uses Python, Node (build only) and uv base images. Review their upstream
notices when redistributing an image; uv is dual MIT/Apache-2.0 and its upstream license files are
available in [the uv repository](https://github.com/astral-sh/uv). Browser audit tools are temporary
development tooling and are not included in the application runtime.

The conditional style block in `templates/admin/change_list.html` is adapted from
Django 5.2's admin template to add a CSP nonce. Django's BSD license is reproduced below.
The upstream template should be reviewed when upgrading Django.

Copyright (c) Django Software Foundation and individual contributors.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright notice,
       this list of conditions and the following disclaimer.

    2. Redistributions in binary form must reproduce the above copyright
       notice, this list of conditions and the following disclaimer in the
       documentation and/or other materials provided with the distribution.

    3. Neither the name of Django nor the names of its contributors may be used
       to endorse or promote products derived from this software without
       specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

