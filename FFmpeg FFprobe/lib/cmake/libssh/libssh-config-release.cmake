#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "ssh" for configuration "Release"
set_property(TARGET ssh APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(ssh PROPERTIES
  IMPORTED_LOCATION_RELEASE "/data/data/com.termux/files/usr/lib/libssh.so"
  IMPORTED_SONAME_RELEASE "libssh.so"
  )

list(APPEND _cmake_import_check_targets ssh )
list(APPEND _cmake_import_check_files_for_ssh "/data/data/com.termux/files/usr/lib/libssh.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
