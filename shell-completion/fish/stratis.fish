# Maintainer: Ariel AxionL <i (at) axionl (dot) me>

# All stratis Arguments
complete -c stratis -s h -l help -d 'Show help message and exit'
complete -c stratis -l version -d "Show program's version number and exit"
complete -c stratis -l propagate -d "Allow exceptions to propagate" # Waiting for further improvement

# All stratis subcommands
set -l cmds 'blockdev daemon filesystem fs pool -h --version --propagate'

function __fish_stratis_pool
    set -l pool_cmds 'create' 'list' 'destroy' 'rename' 'add-data' 'add-cache' '-h'
    set cur_cmds (commandline -opc)

    if [ (count $cur_cmds) -le 2 ]
        for i in $pool_cmds
            echo $i
        end
    else if [ (count $cur_cmds) -le 3 ]
        for i in $cur_cmds
            switch $i
                case 'destroy' 'rename' 'add-data' 'add-cache' # todo: add blockdev completion for add-*
                    __fish_get_stratis_pool
            end
        end
    end
end

function __fish_stratis_blockdev
    set -l blockdev_cmds 'list' '-h'
    set cur_cmds (commandline -opc)
    if [ (count $cur_cmds) -le 2 ]
        for i in $blockdev_cmds
            echo $i
        end
    else if [ (count $cur_cmds) -le 3 ]
        for i in $cur_cmds
            switch $i
                case 'list'
                    __fish_get_stratis_pool
            end
        end
    end
end

function __fish_stratis_filesystem
    set -l filesystem_cmds 'create' 'list' 'snapshot' 'destroy' 'rename' '-h'

    set cur_cmds (commandline -opc)
    if [ (count $cur_cmds) -le 2 ]
        for i in $filesystem_cmds
            echo $i
        end
    else if [ (count $cur_cmds) -le 3 ]
        for i in $cur_cmds
            switch $i
                case 'create' 'list' 'snapshot' 'destroy' 'rename'
                    __fish_get_stratis_pool
            end
        end
    else if [ (count $cur_cmds) -le 4 ]
        for i in $cur_cmds
            switch $i
                case 'snapshot' 'destroy' 'rename'
                    __fish_get_stratis_filesystem
            end
        end
    end
end

function __fish_stratis_daemon
    set -l daemon_cmds 'version' '-h'

    set cur_cmds (commandline -opc)
    if [ (count $cur_cmds) -le 2 ]
        for i in $daemon_cmds
            echo $i
        end
    end
end

function __fish_get_stratis_blockdev
    command stratis blockdev list | sed -n '2,$'p | awk '{print $2}'
end

function __fish_get_stratis_pool
    command stratis pool list | sed -n '2,$'p | awk '{print $1}'
end

function __fish_get_stratis_filesystem
    command stratis filesystem list | sed -n '2,$'p | awk '{print $2}'
end


complete -f -c stratis -n "not __fish_seen_subcommand_from $cmds" -a "$cmds"
complete -f -c stratis -n "__fish_seen_subcommand_from pool" -a "(__fish_stratis_pool)"
complete -f -c stratis -n "__fish_seen_subcommand_from blockdev" -a "(__fish_stratis_blockdev)"
complete -f -c stratis -n "__fish_seen_subcommand_from filesystem" -a "(__fish_stratis_filesystem)"
complete -f -c stratis -n "__fish_seen_subcommand_from fs" -a "(__fish_stratis_filesystem)"
complete -f -c stratis -n "__fish_seen_subcommand_from daemon" -a "(__fish_stratis_daemon)"
