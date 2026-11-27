{# Turn a UTC timestamp into India time (Asia/Kolkata, UTC+5:30), as a plain timestamp. #}
{% macro to_ist(col) -%}
    timezone('Asia/Kolkata', {{ col }})
{%- endmacro %}
