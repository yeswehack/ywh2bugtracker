FROM pandoc/latex:2.11.4

RUN tlmgr update --self
RUN tlmgr install xpatch && \
    tlmgr install realboxes && \
    tlmgr install collectbox && \
    tlmgr install textpos && \
    tlmgr install titlesec
