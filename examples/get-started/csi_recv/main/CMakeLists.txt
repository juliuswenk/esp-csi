idf_component_register(SRC_DIRS "."
                       INCLUDE_DIRS ".")

if(DEFINED RECEIVER_LED_COLOR)
    target_compile_definitions(${COMPONENT_LIB} PRIVATE RECEIVER_LED_COLOR=${RECEIVER_LED_COLOR})
endif()
