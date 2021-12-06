FROM pandoc/latex:2.16.2

RUN tlmgr update --self
RUN tlmgr install xpatch && \
    tlmgr install realboxes && \
    tlmgr install collectbox && \
    tlmgr install textpos && \
    tlmgr install titlesec
