Pipes
=====

Pipes are a one-way buffer of bytes, accessed through a write-only file-like as the input and a read-only file-like as the output.

The state machine of Pipes is like so:

     |
     V         Write
    +-------+  =====>  +----------+
    | Empty |          | Buffered |
    +-------+  <=====  +----------+
        |       Read        |
        | Close             | Close
        | Input             | Input
        V                   V
     /-----\    Read     +----------+
     | EOF |  <========  | Flushing |
     \-----/             +----------+

A Pipe starts Empty. When data is written to it, the Pipe becomes Buffered. It will remain there through additional writes; they do not
block until the buffer is full. When the output is read, the buffer is emptied until there is no more data, then the Pipe enters the Empty
state once again. Reads will return some data if there is any to be had, only blocking if the buffer is completely empty. When the input is
closed, the data in the buffer at the time can be read out, and then reading will return EOF. When the output is closed, writes will begin
failing immediately.

Multiple processes may hold references to a Pipe's input and output. Each end is not considered closed until all references to that end are
closed--a read of a Pipe's output will not EOF until all processes with a reference to the input close it.

A major use of Pipes is for redirecting the standard streams (input, output, and error) of child processes so that the parent may capture
it and process it in some way. Shells also use Pipes to connect several processes into a pipeline.


See Also
--------
* [pipe(7)](http://man7.org/linux/man-pages/man7/pipe.7.html)
