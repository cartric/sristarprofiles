module kalpanatraders/upvc-site

go 1.21

// The Lotus Docs theme is vendored in ./themes/lotusdocs.
// `hugo mod tidy` resolves the theme's own dependencies (Bootstrap SCSS).
replace github.com/colinwilson/lotusdocs => ./themes/lotusdocs

require github.com/gohugoio/hugo-mod-bootstrap-scss/v5 v5.20300.20800 // indirect
