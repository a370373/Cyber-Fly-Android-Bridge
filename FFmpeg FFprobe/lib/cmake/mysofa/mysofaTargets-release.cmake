#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "mysofa::mysofa-static" for configuration "Release"
set_property(TARGET mysofa::mysofa-static APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(mysofa::mysofa-static PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "C"
  IMPORTED_LOCATION_RELEASE "/data/data/com.termux/files/usr/lib/libmysofa.a"
  )

list(APPEND _cmake_import_check_targets mysofa::mysofa-static )
list(APPEND _cmake_import_check_files_for_mysofa::mysofa-static "/data/data/com.termux/files/usr/lib/libmysofa.a" )

# Import target "mysofa::mysofa-shared" for configuration "Release"
set_property(TARGET mysofa::mysofa-shared APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(mysofa::mysofa-shared PROPERTIES
  IMPORTED_LOCATION_RELEASE "/data/data/com.termux/files/usr/lib/libmysofa.so"
  IMPORTED_SONAME_RELEASE "libmysofa.so"
  )

list(APPEND _cmake_import_check_targets mysofa::mysofa-shared )
list(APPEND _cmake_import_check_files_for_mysofa::mysofa-shared "/data/data/com.termux/files/usr/lib/libmysofa.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
