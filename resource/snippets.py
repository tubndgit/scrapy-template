# -*- coding: utf-8 -*-

# Get all text except script/noscript tags
text = '\n'.join([x for x in response.xpath('.//body/descendant-or-self::*[not(self::script) and not(self::noscript)]/text()').extract() if x.strip()])